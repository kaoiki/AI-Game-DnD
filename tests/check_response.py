from core.response import success, error

print(success().model_dump())
print(success(data={"name": "test"}).model_dump())
print(error(message="bad request", code=400).model_dump())