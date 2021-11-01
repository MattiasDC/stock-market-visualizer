import asyncio
import functools

def sync_wrapper(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		return asyncio.run(func(*args, **kwargs))
	
	return wrapper