from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import conn  # importing the MySQL connection
import json


# ---------- QUIZ VIEWS ----------

def quiz_list(request):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Quiz")
    quizzes = cursor.fetchall()
    cursor.close()
    return render(request, 'league/quiz_list.html', {'quizzes': quizzes})


def quiz_detail(request, quiz_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Quiz WHERE id = %s", (quiz_id,))
    quiz = cursor.fetchone()
    cursor.close()

    if not quiz:
        return JsonResponse({'status': 'error', 'message': 'Quiz not found'}, status=404)

    quiz_data = json.loads(quiz['data'])
    return render(request, 'league/quiz_detail.html', {'quiz': quiz, 'quiz_data': quiz_data})


@login_required
def quiz_attempt(request, quiz_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        score = data.get('score', 0)

        cursor = conn.cursor()
        # Insert attempt
        cursor.execute(
            "INSERT INTO QuizAttempt (user_id, quiz_id, score, timestamp) VALUES (%s, %s, %s, %s)",
            (request.user.id, quiz_id, score, timezone.now())
        )

        # Update or create XPBadge
        cursor.execute("SELECT id, xp FROM XPBadge WHERE user_id = %s", (request.user.id,))
        xp_row = cursor.fetchone()
        if xp_row:
            cursor.execute("UPDATE XPBadge SET xp = xp + %s WHERE user_id = %s", (score, request.user.id))
        else:
            cursor.execute("INSERT INTO XPBadge (user_id, xp) VALUES (%s, %s)", (request.user.id, score))

        conn.commit()
        cursor.close()

        return JsonResponse({'status': 'success', 'score': score})

    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})


@login_required
def user_quiz_attempts(request):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM QuizAttempt WHERE user_id = %s ORDER BY timestamp DESC",
        (request.user.id,)
    )
    attempts = cursor.fetchall()
    cursor.close()
    return render(request, 'league/user_attempts.html', {'attempts': attempts})


# ---------- THREAD (DISCUSSION) VIEWS ----------

def thread_list(request):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Thread ORDER BY upvotes DESC")
    threads = cursor.fetchall()
    cursor.close()
    return render(request, 'league/thread_list.html', {'threads': threads})


def thread_detail(request, thread_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Thread WHERE id = %s", (thread_id,))
    thread = cursor.fetchone()
    cursor.close()

    if not thread:
        return JsonResponse({'status': 'error', 'message': 'Thread not found'}, status=404)

    return render(request, 'league/thread_detail.html', {'thread': thread})


@login_required
def thread_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Thread (title, body, author_id, upvotes) VALUES (%s, %s, %s, %s)",
            (title, body, request.user.id, 0)
        )
        conn.commit()
        cursor.close()
        return redirect('thread_list')

    return render(request, 'league/thread_form.html')


@login_required
def thread_upvote(request, thread_id):
    cursor = conn.cursor()
    cursor.execute("UPDATE Thread SET upvotes = upvotes + 1 WHERE id = %s", (thread_id,))
    conn.commit()
    cursor.close()
    return redirect('thread_detail', thread_id=thread_id)


# ---------- XP & BADGE VIEWS ----------

@login_required
def user_xp_badges(request):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM XPBadge WHERE user_id = %s", (request.user.id,))
    xp_badge = cursor.fetchone()

    if not xp_badge:
        xp_badge = {"user_id": request.user.id, "xp": 0}
        cursor.execute("INSERT INTO XPBadge (user_id, xp) VALUES (%s, %s)", (request.user.id, 0))
        conn.commit()

    cursor.close()
    return render(request, 'league/user_xp.html', {'xp_badge': xp_badge})


@login_required
def leaderboard(request):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT XPBadge.user_id, XPBadge.xp, auth_user.username
        FROM XPBadge
        JOIN auth_user ON XPBadge.user_id = auth_user.id
        ORDER BY XPBadge.xp DESC
        LIMIT 20
    """)
    leaderboard = cursor.fetchall()
    cursor.close()
    return render(request, 'league/leaderboard.html', {'leaderboard': leaderboard})
