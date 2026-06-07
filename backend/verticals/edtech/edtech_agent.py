"""
EdTech / Training Vertical — AI assistant for educators, coaching centres, and trainers.

Actions:
  course_outline   — Full course/curriculum outline with modules & outcomes
  quiz_generator   — MCQs / quiz with answer key & difficulty mix
  lesson_plan      — Single-class lesson plan (objectives, activities, assessment)
  progress_report  — Student progress report from marks/observations
  doubt_solver     — Step-by-step explanation of a concept/doubt
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert instructional designer and teacher with deep
pedagogy knowledge (Bloom's taxonomy, scaffolding, formative assessment). You design
clear, age-appropriate, outcome-driven learning material aligned to Indian curricula
(CBSE/ICSE/State boards) and competitive exams when relevant. You are encouraging,
precise, and you always make learning objectives explicit and measurable."""


async def _llm(prompt: str, max_tokens: int = 700) -> str:
    text, _ = await llm_router.complete(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return text


async def course_outline(payload: dict) -> dict:
    prompt = f"""Design a complete course outline.

Course: {payload.get('subject', '')}
Audience / level: {payload.get('level', 'Class 10 / Beginner')}
Total duration: {payload.get('duration', '8 weeks')}
Goal: {payload.get('goal', '')}

Produce:
1. **Course summary** & target outcomes (Bloom-aligned, measurable)
2. **Module breakdown** (per module: title, topics, hours, learning outcomes)
3. **Week-by-week schedule**
4. **Assessment plan** (formative + summative)
5. **Recommended resources / tools**
6. **Capstone / final project idea**"""
    result = await _llm(prompt, 800)
    return {"action": "course_outline", "result": result}


async def quiz_generator(payload: dict) -> dict:
    n = payload.get("num_questions", "10")
    prompt = f"""Generate a quiz.

Topic: {payload.get('topic', '')}
Level: {payload.get('level', 'Class 10')}
Number of questions: {n}
Question types: {payload.get('q_types', 'MCQ + 2 short answer')}
Difficulty mix: {payload.get('difficulty', 'easy/medium/hard mix')}

Produce:
1. **Quiz** — numbered questions. For MCQs give 4 options (A-D).
   Tag each question with difficulty and the concept it tests.
2. **Answer key** with one-line explanation per answer.
3. **Marking scheme** & suggested time.
4. **3 bonus higher-order-thinking questions**."""
    result = await _llm(prompt, 900)
    return {"action": "quiz_generator", "result": result}


async def lesson_plan(payload: dict) -> dict:
    prompt = f"""Create a single-class lesson plan.

Topic: {payload.get('topic', '')}
Grade/level: {payload.get('level', 'Class 8')}
Duration: {payload.get('duration', '45 minutes')}
Class size / context: {payload.get('context', '')}

Produce (structured):
1. **Learning objectives** (3-4, measurable, Bloom verbs)
2. **Prerequisites**
3. **Materials needed**
4. **Lesson flow with timings**: Hook → Direct instruction → Guided practice → Independent practice → Closure
5. **Differentiation** (support + extension learners)
6. **Formative assessment / exit ticket**
7. **Homework"""
    result = await _llm(prompt, 700)
    return {"action": "lesson_plan", "result": result}


async def progress_report(payload: dict) -> dict:
    prompt = f"""Write a constructive student progress report for parents.

Student: {payload.get('student', 'Student')} | Class: {payload.get('level', '')}
Subject(s): {payload.get('subject', '')}
Marks / scores: {payload.get('marks', '')}
Teacher observations: {payload.get('observations', '')}

Produce:
1. **Overall summary** (warm, honest)
2. **Strengths** (specific)
3. **Areas to improve** (actionable, non-judgemental)
4. **Subject-wise note** (if multiple)
5. **Recommended next steps** for student & parent
6. **Encouraging closing line**"""
    result = await _llm(prompt, 600)
    return {"action": "progress_report", "result": result}


async def doubt_solver(payload: dict) -> dict:
    prompt = f"""A student has a doubt. Explain it clearly and pedagogically.

Subject/level: {payload.get('level', '')}
Question / doubt: {payload.get('doubt', '')}

Produce:
1. **Simple explanation** (start from intuition)
2. **Step-by-step working** (if it's a problem)
3. **Worked example**
4. **Common mistakes to avoid**
5. **A practice question** (with hidden answer at the end)
6. **One-line memory tip**"""
    result = await _llm(prompt, 700)
    return {"action": "doubt_solver", "result": result}


async def edtech_agent(action: str, payload: dict, language: str = "en") -> dict:
    """Main EdTech agent dispatcher."""
    action = (action or "").lower().strip()
    handlers = {
        "course_outline":  course_outline,
        "quiz_generator":  quiz_generator,
        "lesson_plan":     lesson_plan,
        "progress_report": progress_report,
        "doubt_solver":    doubt_solver,
    }
    handler = handlers.get(action)
    if not handler:
        return {"error": f"Unknown action '{action}'. Valid: {', '.join(handlers)}"}

    start  = time.monotonic()
    result = await handler(payload)
    result["latency_ms"] = round((time.monotonic() - start) * 1000)
    return result
