class PlanInputModel:
    def __init__(self, plan_id: str, plan_name: str, plan_description: str):
        self.plan_id = plan_id
        self.plan_name = plan_name
        self.plan_description = plan_description

        self.spot_spacing = None
        # only for square patterns
        self.spot_xymin = None
        self.spot_xymax = None
        self.spot_shape = None
        # only for circular patterns
        self.spot_diameter = None
        self.spot_center = None
        self.spot_count = None

        self.spot_mu = None
        self.spot_shape = None  # circular, square, or image
        self.spot_pattern_type = None  # square or hexagonal

        # in case of user loads a png image, this will be the path to the image
        self.spot_image_path = None
