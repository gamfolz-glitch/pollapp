from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Poll, Question, Submission


class PollAccessCodeTests(TestCase):
    def test_access_code_is_generated_on_save(self):
        poll = Poll.objects.create(title="Test poll")
        self.assertTrue(poll.access_code)
        self.assertEqual(len(poll.access_code), 6)
        self.assertTrue(poll.access_code.isalnum())
        self.assertEqual(poll.access_code, poll.access_code.upper())


class PublicPollFlowTests(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(title="My poll", access_code="ABC123")

    def test_code_redirect_works(self):
        resp = self.client.get("/p/", {"code": "abc123"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/p/ABC123/")

    def test_text_question_requires_value(self):
        q = Question.objects.create(
            poll=self.poll,
            text="Your name?",
            kind=Question.Kind.TEXT,
            order=1,
        )

        resp = self.client.post(f"/p/{self.poll.access_code}/", data={f"q_{q.id}": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 0)

        resp = self.client.post(
            f"/p/{self.poll.access_code}/",
            data={f"q_{q.id}": "Alice"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].endswith("/thanks"))
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 1)

    def test_single_choice_requires_one(self):
        q = Question.objects.create(
            poll=self.poll,
            text="Pick one",
            kind=Question.Kind.SINGLE,
            order=1,
        )
        c1 = Choice.objects.create(question=q, text="A")

        resp = self.client.post(f"/p/{self.poll.access_code}/", data={})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 0)

        resp = self.client.post(
            f"/p/{self.poll.access_code}/",
            data={f"q_{q.id}": str(c1.id)},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 1)

    def test_multi_choice_requires_at_least_one(self):
        q = Question.objects.create(
            poll=self.poll,
            text="Pick many",
            kind=Question.Kind.MULTI,
            order=1,
        )
        c1 = Choice.objects.create(question=q, text="A")
        c2 = Choice.objects.create(question=q, text="B")

        resp = self.client.post(f"/p/{self.poll.access_code}/", data={})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 0)

        resp = self.client.post(
            f"/p/{self.poll.access_code}/",
            data={f"q_{q.id}": [str(c1.id), str(c2.id)]},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Submission.objects.filter(poll=self.poll).count(), 1)


class DashboardPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        self.poll = Poll.objects.create(title="Owner poll", owner=self.owner)

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("dashboard_project_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_other_user_cannot_access_owner_poll(self):
        self.client.login(username="other", password="pass12345")
        resp = self.client.get(
            reverse("polls:project_detail", kwargs={"poll_id": self.poll.id})
        )
        self.assertEqual(resp.status_code, 404)
