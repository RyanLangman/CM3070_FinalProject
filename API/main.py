from fastapi import FastAPI, HTTPException
from httpx import AsyncClient

app = FastAPI()

# Mocked data for the endpoints
mocked_data = {
    "name": "John Doe",
    "age": 30,
    "email": "johndoe@example.com",
}

# Endpoint to get the mocked data
@app.get("/get_mocked_data/")
async def get_mocked_data():
    return mocked_data

# Mocked endpoint to fetch data from an external API
@app.get("/get_external_data/")
async def get_external_data():
    # Simulate fetching data from an external API using httpx (mocked)
    # In a real scenario, you would replace this with actual API calls.
    url = "https://api.example.com/data"
    async with AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="External API Error")

# Endpoint using OpenCV to return an image
@app.get("/get_image/")
async def get_image():
    # OpenCV code to read and return an image (mocked)
    # In a real scenario, you would read an actual image file.
    import cv2
    img = cv2.imread("path/to/your/image.jpg")
    _, image_encoded = cv2.imencode(".jpg", img)
    return image_encoded.tobytes()