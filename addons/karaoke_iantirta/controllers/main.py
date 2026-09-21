import typing as t

from sigil.http import Controller, request, route

if t.TYPE_CHECKING:
    from ..models.karaoke_karaoke import KaraokeKaraoke


class KaraokeController(Controller):
    @route("/karaoke/task", type="jsonrpc", auth="bearer")
    def karaoke_task(self, status_to_fetch, **kwargs):
        tasks: KaraokeKaraoke  = request.env["karaoke.karaoke"].search([
            ("status", "==", status_to_fetch)
        ])
        response = []
        for task in tasks:
            response.append({
                "id": task.id,
                "title": task.title,
                "artist": task.artist,
                "duration": task.duration,
                "lyrics": task.lyrics,
                "status": task.status,
                "url": task.source_url,
                "karaoke_type": task.karaoke_type,
            })
        return response
