from app import models
from app.database import SessionLocal
from app.services.tokens import generate_unsubscribe_token

EMAIL = "unsub.test@example.com"


def _make_member():
    db = SessionLocal()
    try:
        member = db.query(models.Member).filter(models.Member.email == EMAIL).first()
        if member is None:
            member = models.Member(email=EMAIL, is_active=True)
            db.add(member)
        member.is_active = True
        db.commit()
    finally:
        db.close()


def _is_active():
    db = SessionLocal()
    try:
        return db.query(models.Member).filter(models.Member.email == EMAIL).first().is_active
    finally:
        db.close()


def test_opening_the_link_does_not_unsubscribe(client):
    _make_member()
    token = generate_unsubscribe_token(EMAIL)
    response = client.get(f"/members/unsubscribe?token={token}")
    assert response.status_code == 200
    assert "Yes, unsubscribe me" in response.text
    assert _is_active() is True


def test_pressing_the_button_unsubscribes(client):
    _make_member()
    token = generate_unsubscribe_token(EMAIL)
    response = client.post(f"/members/unsubscribe?token={token}")
    assert response.status_code == 200
    assert "unsubscribed" in response.text
    assert _is_active() is False


def test_bad_token_changes_nothing(client):
    _make_member()
    client.get("/members/unsubscribe?token=garbage")
    client.post("/members/unsubscribe?token=garbage")
    assert _is_active() is True
