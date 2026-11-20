import csv
import html
import io
from datetime import datetime
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from app.services.tokens import verify_unsubscribe_token
from app.core.security import verify_api_key
from app.core.limiter import limiter

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=List[MemberResponse], dependencies=[Depends(verify_api_key)])
def list_members(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Member)
    if active_only:
        query = query.filter(models.Member.is_active == True)
    return query.all()


@router.get("/export/csv", dependencies=[Depends(verify_api_key)])
def export_members_csv(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Member)
    if active_only:
        query = query.filter(models.Member.is_active == True)
    members = query.order_by(models.Member.added_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "name", "is_active", "added_at"])

    for m in members:
        writer.writerow([m.id, m.email, m.name, m.is_active, m.added_at])

    output.seek(0)
    filename = f"cyai_members_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/", response_model=MemberResponse, dependencies=[Depends(verify_api_key)])
def add_member(member: MemberCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Member).filter(models.Member.email == member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member with this email already exists")

    db_member = models.Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.patch("/{member_id}", response_model=MemberResponse, dependencies=[Depends(verify_api_key)])
def update_member(member_id: int, update: MemberUpdate, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)

    db.commit()
    db.refresh(member)
    return member


@router.post("/bulk-import", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/hour")
def bulk_import_members(request: Request, emails: List[str], db: Session = Depends(get_db)):
    added = 0
    skipped = 0

    for email in emails:
        email = email.strip()
        if not email:
            continue

        existing = db.query(models.Member).filter(models.Member.email == email).first()
        if existing:
            skipped += 1
            continue

        db.add(models.Member(email=email, is_active=True))
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped}


def _page(title: str, message: str, button_html: str = "") -> HTMLResponse:
    body = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title></head>"
        '<body style="font-family: Arial, sans-serif; max-width: 480px; margin: 60px auto; padding: 0 20px; text-align: center;">'
        f"<h2>{html.escape(title)}</h2><p>{html.escape(message)}</p>{button_html}"
        "<p style=\"color: #888; font-size: 12px;\">Cybersecurity &amp; AI Club, York College, CUNY</p>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/unsubscribe")
def unsubscribe_confirm(token: str):
    """Shows a confirmation page only. Nothing changes until the button is pressed.

    Email security scanners open every link in an email. If opening this link
    unsubscribed people, scanners would remove members who never clicked it.
    """
    try:
        email = verify_unsubscribe_token(token)
    except Exception:
        return _page("Link not valid", "This unsubscribe link is invalid or has expired.")

    button = (
        f'<form method="post" action="/members/unsubscribe?token={quote(token, safe="")}">'
        '<button type="submit" style="padding: 12px 24px; font-size: 16px; cursor: pointer;">Yes, unsubscribe me</button>'
        "</form>"
    )
    return _page("Unsubscribe", f"Do you want to stop receiving CYAI newsletters at {email}?", button)


@router.post("/unsubscribe")
def unsubscribe(token: str, db: Session = Depends(get_db)):
    try:
        email = verify_unsubscribe_token(token)
    except Exception:
        return _page("Link not valid", "This unsubscribe link is invalid or has expired.")

    member = db.query(models.Member).filter(models.Member.email == email).first()
    if not member:
        return _page("Not found", "We could not find that email on our member list.")

    member.is_active = False
    db.commit()
    return _page("You are unsubscribed", f"{email} will no longer receive CYAI newsletters.")


@router.delete("/{member_id}", dependencies=[Depends(verify_api_key)])
def remove_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Member removed"}
