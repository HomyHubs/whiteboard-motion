from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
from .hardware import detect_nvidia_gpus, print_report
from .profiles import select_qwen_profile
from .models import ModelManager

def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    if hasattr(sys.stderr, "reconfigure"):
        try: sys.stderr.reconfigure(encoding="utf-8")
        except Exception: pass

    parser = argparse.ArgumentParser(prog="whiteboard-backend")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hardware")
    sub.add_parser("profile")
    media = sub.add_parser("media"); media.add_argument("--prefer", choices=["auto", "nvenc", "x264"])
    sub.add_parser("version"); sub.add_parser("check-update")
    serve = sub.add_parser("serve"); serve.add_argument("--host", default="127.0.0.1"); serve.add_argument("--port", type=int, default=8765)
    credentials = sub.add_parser("credentials")
    cred_sub = credentials.add_subparsers(dest="credential_action", required=True)
    cred_set=cred_sub.add_parser("set");cred_set.add_argument("provider_id");cred_set.add_argument("--key", default=None, help="API key to store (optional, fallback to env WHITEBOARD_API_KEY or getpass)")
    cred_get=cred_sub.add_parser("check");cred_get.add_argument("provider_id")
    cred_delete=cred_sub.add_parser("delete");cred_delete.add_argument("provider_id")
    models = sub.add_parser("models")
    models_sub = models.add_subparsers(dest="action", required=True)
    models_sub.add_parser("list")
    download = models_sub.add_parser("download"); download.add_argument("id")
    accept = models_sub.add_parser("accept"); accept.add_argument("id")
    verify = models_sub.add_parser("verify"); verify.add_argument("id")
    remove = models_sub.add_parser("remove"); remove.add_argument("id")
    voice = sub.add_parser("voice")
    voice_sub = voice.add_subparsers(dest="voice_action", required=True)
    voice_sub.add_parser("list")
    v_create = voice_sub.add_parser("create")
    v_create.add_argument("id")
    v_create.add_argument("--name", default="")
    v_create.add_argument("--language", default="vi", choices=["vi", "en"])
    v_create.add_argument("--reference-audio", type=Path, default=None)
    v_create.add_argument("--reference-text", default="")
    v_create.add_argument("--confirm-consent", action="store_true")
    v_create.add_argument("--statement", default="")
    v_del = voice_sub.add_parser("delete"); v_del.add_argument("id")
    v_audit = voice_sub.add_parser("audit"); v_audit.add_argument("--limit", type=int, default=50)

    args = parser.parse_args(argv)
    if args.command == "hardware": print_report(); return 0
    if args.command == "profile":
        gpus = detect_nvidia_gpus(); print(json.dumps(select_qwen_profile(gpus[0] if gpus else None).to_dict(), ensure_ascii=False, indent=2)); return 0
    if args.command == "version":
        from . import __version__
        print(__version__); return 0
    if args.command == "check-update":
        from .updates import check_for_update
        print(json.dumps(check_for_update(), ensure_ascii=False, indent=2)); return 0
    if args.command == "media":
        from .media import media_report
        report = media_report(args.prefer); print(json.dumps(report, ensure_ascii=False, indent=2)); return 0 if report.get("ffmpeg") else 1
    if args.command == "serve":
        from .server import main as serve_main
        return serve_main(["--host", args.host, "--port", str(args.port)])
    if args.command == "credentials":
        import getpass
        from .security import WindowsCredentialStore,credential_target
        store=WindowsCredentialStore();target=credential_target(args.provider_id)
        if args.credential_action == "set":
            secret = args.key or os.environ.get("WHITEBOARD_API_KEY")
            if not secret: secret=getpass.getpass("API key: ")
            store.set(target,secret);print(f"SAVED={target}");return 0
        if args.credential_action == "check": print(json.dumps({"target":target,"configured":bool(store.get(target))}));return 0
        if args.credential_action == "delete": print(json.dumps({"target":target,"deleted":store.delete(target)}));return 0
    if args.command == "voice":
        from .voices import VoiceProfileStore
        from .security.audit import get_voice_audit_log
        store = VoiceProfileStore()
        if args.voice_action == "list":
            print(json.dumps(store.list(), ensure_ascii=False, indent=2)); return 0
        if args.voice_action == "create":
            created = store.create(
                voice_id=args.id,
                name=args.name or args.id,
                language=args.language,
                is_clone=args.reference_audio is not None,
                reference_audio=args.reference_audio,
                reference_text=args.reference_text,
                consent_confirmed=args.confirm_consent,
                consent_statement=args.statement,
            )
            print(json.dumps(created, ensure_ascii=False, indent=2)); return 0
        if args.voice_action == "delete":
            store.delete(args.id); print(json.dumps({"deleted": True, "id": args.id})); return 0
        if args.voice_action == "audit":
            print(json.dumps(get_voice_audit_log(limit=args.limit), ensure_ascii=False, indent=2)); return 0
    manager = ModelManager()
    if args.action == "list": print(json.dumps(manager.list_status(), ensure_ascii=False, indent=2)); return 0
    if args.action == "download": print(manager.download(args.id)); return 0
    if args.action == "accept": print(manager.accept_license(args.id)); return 0
    if args.action == "verify": print(json.dumps(manager.verify(args.id), ensure_ascii=False, indent=2)); return 0
    if args.action == "remove": manager.remove(args.id); return 0
    return 1


if __name__ == "__main__": raise SystemExit(main())
