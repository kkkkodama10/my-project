"""Task mapping."""
from video_ml.tasks.tasks.extreme_position_task import ExtremePositionTask
from video_ml.tasks.tasks.pixel_size_task import PixelSizeTask
from video_ml.tasks.tasks.position_centroid_task import PositionCentroidTask
from video_ml.tasks.tasks.range_task import RangeTask
from video_ml.data.estimation_models import ExtractFeatureMethodEnum

task_functions = {
    "x_min": {
        "function": ExtremePositionTask,
        "params": {
            "axis": "x",
            "operation": "min"
        }
    },
    "x_max": {
        "function": ExtremePositionTask,
        "params": {
            "axis": "x",
            "operation": "max"
        }
    },
    "y_min": {
        "function": ExtremePositionTask,
        "params": {
            "axis": "y",
            "operation": "min"
        }
    },
    "y_max": {
        "function": ExtremePositionTask,
        "params": {
            "axis": "y",
            "operation": "max"
        }
    },
    "x_range": {
        "function": RangeTask,
        "params": {
            "axis": "x"
        }
    },
    "y_range": {
        "function": RangeTask,
        "params": {
            "axis": "y"
        }
    },
    "pixel_size": {
        "function": PixelSizeTask,
        "params": {}
    },
    "x_centroid_all": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "x",
            "num_segments": 1,
            "segment_index": 0
        }
    },
    "x_centroid_1/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "x",
            "num_segments": 3,
            "segment_index": 0
        }
    },
    "x_centroid_2/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "x",
            "num_segments": 3,
            "segment_index": 1
        }
    },
    "x_centroid_3/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "x",
            "num_segments": 3,
            "segment_index": 2
        }
    },
    "y_centroid_all": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "y",
            "num_segments": 1,
            "segment_index": 0
        }
    },
    "y_centroid_1/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "y",
            "num_segments": 3,
            "segment_index": 0
        }
    },
    "y_centroid_2/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "y",
            "num_segments": 3,
            "segment_index": 1
        }
    },
    "y_centroid_3/3": {
        "function": PositionCentroidTask,
        "params": {
            "axis": "y",
            "num_segments": 3,
            "segment_index": 2
        }
    },
}

task_mapping = {
    ExtractFeatureMethodEnum.POSITION: [
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "x_range",
        "y_range",
    ],
    ExtractFeatureMethodEnum.MOVEMENT: [
        "x_centroid_all",
        "y_centroid_all",
        "x_centroid_1/3",
        "x_centroid_2/3",
        "x_centroid_3/3",
        "y_centroid_1/3",
        "y_centroid_2/3",
        "y_centroid_3/3",
    ],
    ExtractFeatureMethodEnum.SIZE: [
        "pixel_size",
    ],
    ExtractFeatureMethodEnum.EXISTING: [
        "pixel_size",
    ],
}
