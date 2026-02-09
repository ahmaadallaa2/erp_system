import threading
from django.utils.deprecation import MiddlewareMixin

# مخزن مؤقت لكل Request (Thread Local Storage)
_thread_locals = threading.local()

def get_current_user():
    """
    دالة بترجع اليوزر الحالي اللي عمل الريكويست.
    لو مفيش يوزر (زي الـ Terminal)، بترجع None.
    """
    return getattr(_thread_locals, 'user', None)

class ThreadLocalMiddleware(MiddlewareMixin):
    """
    ميدلوير بياخد اليوزر من الـ Request ويحطه في المخزن المؤقت
    عشان المودلز تقدر تشوفه من غير ما نمرره يدوياً.
    """
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)