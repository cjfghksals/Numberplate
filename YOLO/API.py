from roboflow import Roboflow

rf = Roboflow(api_key="L5lQmKFYOosdYUeNZSGT")
project = rf.workspace("license-plate-mhig5").project("license-plate-7egee")
version = project.version(5)
dataset = version.download("yolov8")
