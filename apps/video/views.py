from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import os
from django.http import StreamingHttpResponse, Http404
from django.conf import settings

import os
from django.http import FileResponse, Http404
from django.conf import settings


def stream_video(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, "videos", "test", filename)

    if not os.path.exists(file_path):
        raise Http404

    file_size = os.path.getsize(file_path)

    range_header = request.headers.get("Range", "").strip()
    if range_header:
        range_match = range_header.split("=")[1]
        start_str, end_str = range_match.split("-")

        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
        length = end - start + 1

        f = open(file_path, "rb")
        f.seek(start)

        response = FileResponse(f, status=206, content_type="video/mp4")
        response["Content-Length"] = str(length)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"

        return response

    return FileResponse(open(file_path, "rb"), content_type="video/mp4")

# Create your views here.
@login_required
def video_player(request):
    return render(request, "video/player.html", {
        "subtitle_json": "/media/subtitles/test/video_name.tokens.json",
    })

