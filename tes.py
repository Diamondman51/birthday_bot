# # from functools import wraps

# # def my_decorator(func):
# #     def wrapper(*args, **kwargs):
# #         print("Before call")
# #         return func(*args, **kwargs)
# #     return wrapper

# # @my_decorator
# def say_hello():
#     """This function says hello."""
#     print("Hello")

# # print(say_hello.__name__)     # ❌ Outputs: 'wrapper'
# # print(say_hello.__doc__)      # ❌ Outputs: None




# from functools import wraps

# def my_decorator(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         print("Before call")
#         return func(*args, **kwargs)
#     return wrapper

# @my_decorator
# def say_hello():
#     """This function says hello."""
#     print("Hello")

# # print(say_hello.__name__)     # ✅ Outputs: 'say_hello'
# # print(say_hello.__doc__)      # ✅ Outputs: 'This function says hello.'

# from pydantic import BaseModel
# from datetime import time

# class Schedule(BaseModel):
#     start_time: time
#     end_time: time



# # Valid input (string is automatically parsed)
# s = Schedule(start_time="08:30", end_time="17:00")
# print(s.start_time, type(s.start_time))  # 08:30:00

# # Invalid time format
# Schedule(start_time="25:00", end_time="17:00")
# # ❌ ValidationError: time does not match format


# Notification
# from plyer import notification

# notification.notify(
#     title='Reminder',
#     message='Take a break and stretch!',
#     app_name='Python',
#     timeout=10
# )
