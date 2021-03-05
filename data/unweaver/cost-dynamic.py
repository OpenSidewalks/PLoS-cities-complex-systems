"""Defines cost function generators for optimal path finding."""
def cost_fun_generator(
    downhill=0.1, uphill=0.085, avoid_curbs=True, elevators=False, base_speed=1, min_width=1,
):
    def cost_fun(u, v, d):
        width = d.get("width", None)
        if width is not None and width < min_width:
            return None
        layer = d["_layer"]
        length = d["length"]
        incline = d.get("incline", None)

        if layer == "sidewalks":
            if length > 3:
                if incline > uphill:
                    return None
                if incline < -downhill:
                    return None
        elif layer == "crossings":
            # Avoid raised curbs based on user setting
            if avoid_curbs and not d["curbramps"]:
                return None
        elif layer == "elevator_paths":
            if not elevators:
                return None
        else:
            # This shouldn't happen. Raise error?
            return None

        return length

    return cost_fun
