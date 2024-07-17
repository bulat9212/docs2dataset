# File: docs2dataset/preprocessing/pipeline_processor.py
import importlib
from docs2dataset.preprocessing.image_processor_interface import ImageProcessorInterface

class PipelineProcessor:
    def __init__(self, pipeline_config):
        self.pipeline = self._create_pipeline(pipeline_config)

    @staticmethod
    def _create_pipeline(config):
        pipeline = []
        for step in config:
            # Convert CamelCase to snake_case for file names
            module_name = ''.join(['_' + i.lower() if i.isupper() else i for i in step['instance_name']]).lstrip('_')
            module_path = f"docs2dataset.preprocessing.processors.{module_name}"
            class_name = step['instance_name']

            module = importlib.import_module(module_path)
            processor_class = getattr(module, class_name)

            processor = processor_class(step.get('params', {}))
            pipeline.append(processor)
        return pipeline

    def run(self, image):
        for processor in self.pipeline:
            image = processor.process(image)
        return image
