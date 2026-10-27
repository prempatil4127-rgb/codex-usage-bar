"""Read foreground-window metadata; move only the meter's own window."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import PureWindowsPath

u = c.WinDLL('user32', use_last_error=True)
k = c.WinDLL('kernel32', use_last_error=True)


def bind(lib, name, result, *args):
    fn = getattr(lib, name)
    fn.restype, fn.argtypes = result, args
    return fn


foreground = bind(u, 'GetForegroundWindow', w.HWND)
get_parent = bind(u, 'GetParent', w.HWND, w.HWND)
get_pid = bind(u, 'GetWindowThreadProcessId', w.DWORD, w.HWND, c.POINTER(w.DWORD))
get_rect = bind(u, 'GetWindowRect', w.BOOL, w.HWND, c.POINTER(w.RECT))
is_iconic = bind(u, 'IsIconic', w.BOOL, w.HWND)
open_process = bind(k, 'OpenProcess', w.HANDLE, w.DWORD, w.BOOL, w.DWORD)
close_handle = bind(k, 'CloseHandle', w.BOOL, w.HANDLE)
image_name = bind(k, 'QueryFullProcessImageNameW', w.BOOL, w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD))
set_pos = bind(u, 'SetWindowPos', w.BOOL, w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT)
show = bind(u, 'ShowWindow', w.BOOL, w.HWND, c.c_int)
get_style = bind(u, 'GetWindowLongPtrW', c.c_ssize_t, w.HWND, c.c_int)
set_style = bind(u, 'SetWindowLongPtrW', c.c_ssize_t, w.HWND, c.c_int, c.c_ssize_t)
create_mutex = bind(k, 'CreateMutexW', w.HANDLE, c.c_void_p, w.BOOL, w.LPCWSTR)


def is_codex_path(path):
    p = PureWindowsPath(path)
    return (p.name.lower() in ('chatgpt.exe', 'codex.exe')
            and any(part.lower().startswith('openai.codex_') for part in p.parts))


def host_rect():
    hwnd = foreground()
    if not hwnd or is_iconic(hwnd):
        return None
    pid = w.DWORD()
    get_pid(hwnd, c.byref(pid))
    process = open_process(0x1000, False, pid.value)
    if not process:
        return None
    try:
        name, size = c.create_unicode_buffer(32768), w.DWORD(32768)
        if not image_name(process, 0, name, c.byref(size)) or not is_codex_path(name.value):
            return None
    finally:
        close_handle(process)
    rect = w.RECT()
    if get_rect(hwnd, c.byref(rect)):
        return rect.left, rect.top, rect.right, rect.bottom


def no_activate(hwnd):
    set_style(hwnd, -20, (get_style(hwnd, -20) | 0x08000080) & ~0x00040000)


_placements = {}


def place(hwnd, x, y, width, height):
    bounds = (x, y, width, height)
    if _placements.get(hwnd) != bounds:
        if set_pos(hwnd, w.HWND(-1), *bounds, 0x0010 | 0x0040):
            _placements[hwnd] = bounds


def hide(hwnd):
    if hwnd in _placements:
        show(hwnd, 0)
        del _placements[hwnd]
