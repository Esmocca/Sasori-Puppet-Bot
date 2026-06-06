cd C:\Users\ardan\OneDrive\Desktop\yolov7-main-person
//Masuk ke folder Yolov7-main-person

(base) C:\Users\ardan\OneDrive\Desktop\yolov7-main-person>conda activate myenvi
//activate myenvi

//Step sama seperti di GitHub robot 3


//Cara convert ke onnx 

(myenvi) C:\Users\ardan\OneDrive\Desktop\yolov7-main-person>python export.py --weights runs/train/yolov7/weights/person.pt --img-size 480 320 --grid
Namespace(weights='runs/train/yolov7/weights/person.pt', img_size=[480, 320], batch_size=1, dynamic=False, dynamic_batch=False, grid=True, end2end=False, max_wh=None, topk_all=100, iou_thres=0.45, conf_thres=0.25, device='cpu', simplify=False, include_nms=False, fp16=False, int8=False)

python export.py --weights runs/train/yolov7/weights/person.pt --img-size 480 320 --grid --simplify

python export.py --weights runs/train/yolov7/weights/person.pt --img-size 480 320 --grid

copy file onnx ke dalam folder yang sama pada main.py dan inference .py
