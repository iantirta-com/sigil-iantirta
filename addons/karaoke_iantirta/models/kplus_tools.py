import kplus
from kplus.pipelines import (
    extract_info,
    extract_lyrics,
)
from kplus.worker.gpu_worker import KaggleWorker

if __name__ == "__main__":
    print("Test Kplus")
    from kplus.tools import rich
    rich.print("rich Ok")
    rich.inspect(kplus.worker.gpu_worker.KaggleWorker, methods=True)