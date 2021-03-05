import copy

import shapely
from shapely.geometry import shape

import unweaver

# 30-meter search distance
SEARCH_DISTANCE = 30

# TODO: put in top-level __init__, as it has global effects?
if shapely.speedups.available:
    shapely.speedups.enable()


def reach_metrics(networks, street_edge, interpolate=0.5):
    # FIXME: standardize expectation over profile combinations. Is it
    # all-by-all comparisons between ped and street? Need a strategy for
    # aligning pedestrian profiles with street profiles. For now, assumes only
    # a single street profile
    geom_key_st = networks.street.G.network.edges.geom_column
    geom_key_ped = networks.pedestrian.G.network.edges.geom_column
    G_ped = networks.pedestrian.G
    street_profile = networks.street.profiles[0]
    # TODO: use precalculated weights
    street_cost_function = street_profile["cost_function"]()

    # Get the midpoint
    geometry_st = shape(street_edge[geom_key_st])
    # TODO: ensure interpolation happens geodetically - currently introduces
    # errors as it's done in wgs84
    midpoint = geometry_st.interpolate(interpolate, normalized=True)
    # Get the associated sidewalks, if applicable
    sidewalk_ids = []
    # FIXME: Why would sw_left exist but not pkey_left?
    if "sw_left" in street_edge and street_edge["pkey_left"] is not None:
        sidewalk_ids.append(street_edge["pkey_left"])
    if "sw_right" in street_edge and street_edge["pkey_right"] is not None:
        sidewalk_ids.append(street_edge["pkey_right"])

    if not sidewalk_ids:
        return {profile["id"]: 0 for profile in networks.pedestrian.profiles}

    street_candidates = unweaver.graph.waypoint_candidates(
        networks.street.G,
        midpoint.x,
        midpoint.y,
        4,
        is_destination=False,
        dwithin=SEARCH_DISTANCE,
    )

    street_candidate = unweaver.graph.choose_candidate(
        street_candidates, street_cost_function
    )
    if street_candidate is None:
        # FIXME: handle this better
        raise Exception("No street candidate!?")

    to_retrieve = set([int(sw_id) for sw_id in sidewalk_ids])
    sidewalks = []
    near_edges = G_ped.edges_dwithin(
        midpoint.x, midpoint.y, distance=SEARCH_DISTANCE, sort=True
    )
    near = list(near_edges)
    for u, v, d in near:
        # FIXME: hard-coded, prevents use of other datasets
        if d["_layer"] == "sidewalks":
            if d["pkey"] in to_retrieve:
                sidewalks.append(d)
                to_retrieve.remove(d["pkey"])

    # Find reachable paths for all
    sw_distances = {
        profile["id"]: [] for profile in networks.pedestrian.profiles
    }
    sw_candidates_list = []
    for sidewalk in sidewalks:
        sw_geometry = shape(sidewalk[geom_key_ped])
        sw_midpoint = sw_geometry.interpolate(sw_geometry.project(midpoint))
        sw_candidates = list(
            unweaver.graph.waypoint_candidates(
                networks.pedestrian.G,
                sw_midpoint.x,
                sw_midpoint.y,
                1,
                is_destination=False,
                dwithin=SEARCH_DISTANCE,
            )
        )
        sw_candidates_list.append(sw_candidates)

    for profile in networks.pedestrian.profiles:
        profile_id = profile["id"]

        cost_function_static = default_static_cost_function(profile_id)
        cost_function = profile["cost_function"]()

        for sw_candidates in sw_candidates_list:
            for candidate in sw_candidates:
                for attr in ("edge1", "edge2"):
                    edge = getattr(candidate, attr)
                    if edge is not None:
                        u, v, d = edge
                        d = dict(d)
                        d[f"_weight_{profile_id}"] = cost_function(u, v, d)
                        setattr(candidate, attr, (u, v, d))

            sw_candidate = unweaver.graph.choose_candidate(
                copy.deepcopy(sw_candidates), cost_function_static
            )

            if sw_candidate is None:
                # No valid candidate could be identified - falls outside cost
                # fun
                sw_distances[profile_id].append(0)
            else:
                G_aug = unweaver.graphs.augmented.prepare_augmented(
                    networks.pedestrian.G, sw_candidate
                )
                sw_nodes, sw_edges = unweaver.algorithms.reachable.reachable(
                    G_aug, sw_candidate, cost_function_static, max_cost=400
                )
                sw_distance = 0
                seen_edges = set([])
                for edge in sw_edges:
                    # TODO: embed ID in all edges? pkey is unique to seattle
                    if "pkey" in edge:
                        if edge["pkey"] not in seen_edges:
                            sw_distance += edge["length"]
                            seen_edges.add(edge["pkey"])
                # sw_distance = sum([edge["length"] for edge in sw_edges])
                sw_distances[profile_id].append(sw_distance)

    sw_total_distances = {
        name: sum(distances) for name, distances in sw_distances.items()
    }

    G_aug = unweaver.graphs.augmented.prepare_augmented(
        networks.street.G, street_candidate
    )
    st_nodes, st_edges = unweaver.algorithms.reachable.reachable(
        G_aug, street_candidate, street_cost_function, max_cost=400
    )
    st_total_distance = sum([edge["length"] for edge in st_edges])

    final_scores = {}
    for name, total_distance in sw_total_distances.items():
        # Calculate reach_metrics
        if not st_total_distance:
            # FIXME: consider whether this is a valid conclusion
            final_scores[name] = 0
        else:
            # Normalized sidewalk metric reach is normalized by 2 to account
            # for the fact that we asked for distances on up to 2 sidewalks.
            final_scores[name] = total_distance / 2 / st_total_distance

    # TODO: save and return walksheds as well

    return final_scores


def default_static_cost_function(profile_id):
    key = f"_weight_{profile_id}"

    def cost_function(u, v, d):
        return d.get(key, None)

    return cost_function
