from enum import Enum

class DataBaseEnum(Enum):

    COLLECTION_PROJECT_NAME = "project"
    COLLECTION_CHUNKS_NAME = "chunks"
    COLLECTION_ASSETS_NAME = "assets" 
    USER = "user"
    PROJECT = "project"
    MODEL = "model"
    MODEL_VERSION = "model_version"
    JOB = "job"
    JOB_STATUS = "job_status"
    JOB_TYPE = "job_type"
    JOB_RESULT = "job_result"
    JOB_RESULT_TYPE = "job_result_type"
    JOB_RESULT_STATUS = "job_result_status"
    JOB_RESULT_ERROR = "job_result_error"
    JOB_RESULT_ERROR_TYPE = "job_result_error_type"
    JOB_RESULT_ERROR_STATUS = "job_result_error_status"