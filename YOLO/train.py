from ultralytics import YOLO

def main():
    model = YOLO(r"C:\Users\moble_pc\Desktop\yungeun\model\yolov8n.pt")

    results = model.train(
        data=r"C:\Users\moble_pc\Desktop\yungeun\license-plate-5\data.yaml",
        imgsz=640,
        epochs=100,
        batch=64,
        name="64_100",
    )


if __name__ == '__main__':
    main()
