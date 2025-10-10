from fastapi import FastAPI
from routes import base ,data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from  helper.config import get_settings
from stores.llm.LLmProverFactory import LLmProverFactory
from stores.Vector_db.VectorDbFactory import VectorDbFactory




app = FastAPI()

async def startup_span():
    settings = get_settings()
    app.mongodb_client = AsyncIOMotorClient(settings.DATABASE_URL)
    app.mongodb = app.mongodb_client[settings.DATABASE_NAME]
    
    llm_proveder_factory = LLmProverFactory(settings)
    vector_db_factory = VectorDbFactory(settings)

    # gen cleint
    app.generation_client = llm_proveder_factory.create(
        provider = settings.GENERATION_BACKEND,
    ) 
    if app.generation_client:
        app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    else:
        raise Exception("Failed to initialize generation client")

    # embed client
    app.embedding_client = llm_proveder_factory.create(
        provider = settings.EMBEDDING_BACKEND,
    )
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID,settings.EMBEDDING_MODEL_SIZE)



    # vector db client
    app.vector_db_client = vector_db_factory.create(
        provider = settings.VECTOR_DB_BACKEND,
    )
    if not app.vector_db_client:
        raise RuntimeError(f"Vector DB client not created for provider: {settings.VECTOR_DB_BACKEND}")
    app.vector_db_client.connect()


async def shutdown_span():
    app.mongodb_client.close()
    app.vector_db_client.disconnect()


# app.router.lifespan.onstartup.append(startup_span)
# app.router.lifespan.onshutdown.append(shutdown_span)

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)

