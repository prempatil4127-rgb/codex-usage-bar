"""Read-only token meter for one Codex chat. Run with its session JSONL path."""
import json
import sys
import os
from pathlib import Path


def latest_usage(path):
    # shortcut: scan the last 2 MB; increase if usage events become farther apart.
    with path.open('rb') as stream:
        stream.seek(0, 2)
        start = max(0, stream.tell() - 2 * 1024 * 1024)
        stream.seek(start)
        if start:
            stream.readline()
        lines = stream.read().splitlines()
    for line in reversed(lines):
        if b'"token_count"' not in line:
            continue
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        payload = event.get('payload', {})
        if payload.get('type') == 'token_count' and payload.get('info'):
            return event['timestamp'], payload['info'], payload.get('rate_limits')
    raise ValueError('Waiting for a recorded usage event')


def quota_display(limits, key, now):
    window = (limits or {}).get(key) or {}
    used = window.get('used_percent')
    minutes = window.get('window_minutes')
    resets = window.get('resets_at')
    if used is None or minutes is None:
        return 'Quota unavailable', 0
    name = 'Weekly' if minutes == 10080 else f'{minutes / 60:g}-hour'
    if resets is not None and now >= resets:
        return f'{name}: awaiting usage update after reset', 0
    return f'{name}: {used:g}% used · {max(0, 100 - used):g}% remaining', max(0, min(100, used))



def latest_session(directory):
    return max(directory.glob('*/*/*/*.jsonl'), key=lambda p: p.stat().st_mtime, default=None)


def anchor(rect, width, height, dx=0, dy=0):
    left, top, right, bottom = rect
    return (max(left, min(right - width, right - width - 24 + dx)),
            max(top, min(bottom - height, bottom - height - 12 + dy)))


def main(path=None):
    import ctypes
    import tkinter as tk
    from datetime import datetime
    import windows_host as win

    base = Path(__file__).resolve().parent
    codex_home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser()
    if (base / 'runtime.json').exists():
        codex_home = Path(json.loads((base / 'runtime.json').read_text(encoding='utf-8-sig'))['codexHome'])
    mutex = win.create_mutex(None, False, 'Local\\CodexUsageCompanion')
    if not mutex:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        win.close_handle(mutex)
        return
    root = tk.Tk()
    root.title('Codex · Usage companion')
    root.overrideredirect(True)
    root.configure(bg='#232b2a')
    root.attributes('-toolwindow', True)
    width, height = 362, 44
    root.geometry(f'{width}x{height}+0+0')
    canvas = tk.Canvas(root, width=width, height=height, bg='#232b2a', highlightthickness=1,
                       highlightbackground='#3c4945', cursor='fleur')
    canvas.pack(fill='both', expand=True)
    root.update_idletasks()
    hwnd = win.get_parent(root.winfo_id()) or root.winfo_id()
    win.no_activate(hwnd)
    root.withdraw()
    tip = tk.Toplevel(root)
    tip.overrideredirect(True)
    tip.configure(bg='#232b2a')
    tip_text = tk.Label(tip, bg='#232b2a', fg='#e5eee9', justify='left',
                        font=('Segoe UI', 10), padx=14, pady=12)
    tip_text.pack()
    tip.update_idletasks()
    tip_hwnd = win.get_parent(tip.winfo_id()) or tip.winfo_id()
    win.no_activate(tip_hwnd)
    tip.withdraw()
    offset = [0, 0]
    try:
        saved = json.loads((base / 'position.json').read_text())
        if len(saved) == 2 and all(isinstance(n, int) for n in saved):
            offset[:] = saved
    except (OSError, ValueError, TypeError):
        pass
    hover = False
    drag = None
    last_source_check = 0
    selected = path
    current_rect = None
    usage_signature = None
    cached_usage = None
    last_paint = None

    def paint(info=None, limits=None):
        nonlocal last_paint
        quotas = tuple(quota_display(limits, key, datetime.now().timestamp())
                       for key in ('primary', 'secondary'))
        state = (info, quotas)
        if state == last_paint:
            return
        last_paint = state
        canvas.delete('all')
        canvas.create_line(17, 26, 17, 18, fill='#a9cdb6', width=2)
        canvas.create_oval(10, 13, 17, 19, fill='#a9cdb6', outline='')
        canvas.create_oval(18, 10, 25, 17, fill='#a9cdb6', outline='')
        tokens = info['total_token_usage']['total_tokens'] if info else None
        caption = f'{tokens / 1e6:.2f}M' if tokens is not None and tokens >= 1e6 else f'{tokens / 1000:.1f}k' if tokens is not None else '—'
        canvas.create_text(35, 16, text=caption, fill='#edf3ef', font=('Segoe UI', 11, 'bold'), anchor='w')
        canvas.create_text(35, 32, text='tokens · latest chat', fill='#b3c2ba', font=('Segoe UI', 8), anchor='w')
        for (x, key), (text, value) in zip(((155, 'primary'), (258, 'secondary')), quotas):
            valid = '% used' in text
            name = text.split(':')[0] if ':' in text else ('5-hour' if key == 'primary' else 'Weekly')
            canvas.create_text(x, 15, text=f'{name}  {value:g}%' if valid else f'{name}  —',
                               fill='#e2eae5', font=('Segoe UI', 9), anchor='w')
            canvas.create_line(x, 31, x + 82, 31, fill='#45534b', width=3)
            if valid and value:
                canvas.create_line(x, 31, x + 82 * value / 100, 31,
                                   fill='#d9b57a' if value >= 80 else '#a9cdb6', width=3)

    def refresh():
        nonlocal selected, last_source_check, usage_signature, cached_usage
        if current_rect is None or drag is not None:
            root.after(2000, refresh)
            return
        try:
            now = datetime.now().timestamp()
            if not path and now - last_source_check >= 10:
                selected = latest_session(codex_home / 'sessions')
                last_source_check = now
            if selected is None:
                raise ValueError('No local chat usage yet')
            stat = selected.stat()
            signature = (selected, stat.st_mtime_ns, stat.st_size)
            if signature != usage_signature:
                cached_usage = latest_usage(selected)
                usage_signature = signature
            stamp, info, limits = cached_usage
            paint(info, limits)
            usage = info['total_token_usage']
            recorded = datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone().strftime('%d %b, %H:%M:%S')
            details = (f"Latest active local chat · {selected.stem[-8:]}\n"
                       f"{usage['total_tokens']:,} tokens (includes repeated input)\n"
                       f"Input {usage['input_tokens']:,} · Output {usage['output_tokens']:,}\n"
                       f"Cached input {usage.get('cached_input_tokens', 0):,}\n\n"
                       + '\n'.join(quota_display(limits, key, now)[0] for key in ('primary', 'secondary'))
                       + f'\nDaily quota: not reported\nRecorded {recorded}\n\nDrag to reposition · Right-click to quit')
        except (OSError, ValueError, KeyError, TypeError) as error:
            paint()
            details = f'Usage unavailable: {error}\nWaiting for the next recorded update.'
        if tip_text.cget('text') != details:
            tip_text.config(text=details)
        root.after(2000, refresh)

    def follow():
        nonlocal current_rect
        rect = win.host_rect()
        current_rect = rect
        if rect and rect[2] - rect[0] >= width and rect[3] - rect[1] >= height:
            x, y = anchor(rect, width, height, *offset)
            win.place(hwnd, x, y, width, height)
            if hover and drag is None:
                tw, th = tip.winfo_reqwidth(), tip.winfo_reqheight()
                win.place(tip_hwnd, min(x, rect[2] - tw), max(rect[1], y - th - 6), tw, th)
            else:
                win.hide(tip_hwnd)
        else:
            win.hide(hwnd)
            win.hide(tip_hwnd)
        root.after(100 if rect else 500, follow)

    def enter(event):
        nonlocal hover
        hover = True

    def leave(event):
        nonlocal hover
        hover = False
        win.hide(tip_hwnd)

    def start_drag(event):
        nonlocal drag
        drag = (event.x_root, event.y_root, *offset)

    def move_drag(event):
        if drag:
            offset[:] = [drag[2] + event.x_root - drag[0], drag[3] + event.y_root - drag[1]]
            if current_rect:
                x, y = anchor(current_rect, width, height, *offset)
                win.place(hwnd, x, y, width, height)

    def end_drag(event):
        nonlocal drag
        drag = None
        try:
            (base / 'position.json').write_text(json.dumps(offset))
        except OSError:
            pass

    canvas.bind('<Enter>', enter)
    canvas.bind('<Leave>', leave)
    canvas.bind('<ButtonPress-1>', start_drag)
    canvas.bind('<B1-Motion>', move_drag)
    canvas.bind('<ButtonRelease-1>', end_drag)
    canvas.bind('<Button-3>', lambda event: root.destroy())
    paint()
    follow()
    refresh()
    try:
        root.mainloop()
    finally:
        win.close_handle(mutex)


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
