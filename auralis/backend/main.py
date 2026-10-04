from fastapi import FastAPI

# Create the API application used by Uvicorn.
app = FastAPI()


@app.get("/")
def read_root():
	# Provide a simple confirmation that the backend is running.
	return {"message": "Auralis backend is running"}


@app.get("/health")
def health_check():
	# Let tools check that the API is responding.
	return {"status": "ok"}