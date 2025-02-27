from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id="unstructuredio/yolo_x_layout",
    filename="yolox_l0.05.onnx",
    force_download=True,
)
