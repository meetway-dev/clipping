import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.viral_detector import ViralDetector
from core.sentence_aligner import SemanticSentenceAligner

def generate_mock_podcast_transcript():
    """
    Constructs a realistic 6-minute (360 seconds) podcast segment transcript
    with multiple topics:
    - Topic A: Question & Answer (~72 seconds total) - Ideal 60-90s sweet spot.
    - Topic B: A punchy story with anchor start & punchline (~68 seconds) - 60-90s sweet spot.
    - Topic C: A long, deep comprehensive breakdown of a framework (~155 seconds) - Long complete clip.
    - Topic D: Short filler (~25 seconds).
    """
    segments = []
    t = 0.0

    # Topic A: Question & Answer (0s to ~75s)
    # Question:
    q_words = ["Have", "you", "ever", "wondered", "why", "most", "creators", "burn", "out", "within", "six", "months?"]
    seg_dur = 4.5
    segments.append({
        "start": t, "end": t + seg_dur,
        "text": "Have you ever wondered why most creators burn out within six months?",
        "words": [{"word": w, "start": t + i*(seg_dur/len(q_words)), "end": t + (i+1)*(seg_dur/len(q_words))} for i, w in enumerate(q_words)]
    })
    t += seg_dur + 0.3

    # Answer spanning ~68 seconds of thoughtful dialogue:
    answer_sentences = [
        "The truth is they focus entirely on dopamine and short-term metrics instead of sustainable creative stamina.",
        "When I started making content in 2019, I worked fourteen hours every day without a break.",
        "My sleep was destroyed, my relationships suffered, and my content actually became worse because of exhaustion.",
        "Then I made one fundamental shift in my daily schedule that changed everything.",
        "I blocked out three uninterrupted morning hours for deep creative focus and protected my evenings completely.",
        "That single boundary doubled my production while cutting my stress in half.",
        "That is the real secret to staying in the game long enough to actually win."
    ]
    for sent in answer_sentences:
        w_list = sent.split()
        dur = len(w_list) * 0.48
        segments.append({
            "start": t, "end": t + dur,
            "text": sent,
            "words": [{"word": w, "start": t + i*(dur/len(w_list)), "end": t + (i+1)*(dur/len(w_list))} for i, w in enumerate(w_list)]
        })
        t += dur + 0.4

    # Topic B: Punchy Story (~68 seconds)
    t += 2.0  # pause between topics
    story_sentences = [
        "The biggest mistake most people make with their money is keeping too much cash in a checking account.",
        "Inflation quietly eats away at your purchasing power every single month.",
        "A friend of mine had fifty thousand dollars sitting in a zero-interest savings account for six years.",
        "He thought he was being conservative and responsible.",
        "In reality, inflation stole nearly ten thousand dollars of value without him ever noticing a thing.",
        "You have to put your capital to work in productive assets that compound over time.",
        "That's why understanding real assets is the only way to protect your financial freedom."
    ]
    for sent in story_sentences:
        w_list = sent.split()
        dur = len(w_list) * 0.52
        segments.append({
            "start": t, "end": t + dur,
            "text": sent,
            "words": [{"word": w, "start": t + i*(dur/len(w_list)), "end": t + (i+1)*(dur/len(w_list))} for i, w in enumerate(w_list)]
        })
        t += dur + 0.4

    # Topic C: Long In-Depth Breakdown (~160 seconds)
    t += 2.5
    long_sentences = [
        "Now let me explain the three fundamental pillars of building a high-ticket service business in 2026.",
        "Pillar number one is having an undeniable offer that solves a painful, urgent problem for an affluent customer.",
        "If the customer does not wake up thinking about this problem, you are fighting an uphill battle from day one.",
        "You need to speak directly to the exact bottleneck that costs them time or revenue.",
        "Pillar number two is building an automated inbound pipeline rather than relying on endless manual outreach.",
        "When you publish high-value breakdown content, qualified prospects come to you pre-sold on your methodology.",
        "They already trust your competence before they ever schedule a discovery call.",
        "Pillar number three is delivering a world-class onboarding experience that guarantees client success.",
        "Most agencies lose clients not because the strategy failed, but because communication during the first fourteen days was messy.",
        "If you eliminate friction early, your retention goes through the roof and referrals become automatic.",
        "We implemented this exact three-pillar framework across twenty different businesses last year.",
        "Every single business saw their average customer lifetime value double within ninety days.",
        "Which changed everything for our growth trajectory and gave us ultimate leverage in the marketplace."
    ]
    for sent in long_sentences:
        w_list = sent.split()
        dur = len(w_list) * 0.58
        segments.append({
            "start": t, "end": t + dur,
            "text": sent,
            "words": [{"word": w, "start": t + i*(dur/len(w_list)), "end": t + (i+1)*(dur/len(w_list))} for i, w in enumerate(w_list)]
        })
        t += dur + 0.45

    return segments

def test_sweet_spot_and_long_clips():
    print("============================================================")
    print("Testing AI Duration Sweet-Spot (60-90s) & Long Narrative Selection")
    print("============================================================")

    segments = generate_mock_podcast_transcript()
    total_dur = segments[-1]["end"]
    print(f"Total mock transcript duration: {total_dur:.1f}s ({total_dur/60:.1f} minutes)")

    detector = ViralDetector()

    # Case 1: User selects min 60s, max 180s
    print("\n[Test 1] User selects min_seconds = 60.0, max_seconds = 180.0:")
    clips = detector.find_viral_clips(
        segments=segments,
        min_seconds=60.0,
        max_seconds=180.0,
        top_k=4,
        clip_mode="highlights"
    )
    assert len(clips) >= 2, f"Expected at least 2 clips, got {len(clips)}"

    sweet_spot_count = 0
    long_count = 0

    for i, c in enumerate(clips, 1):
        dur = c["duration"]
        print(f"  Clip {i}: Title: '{c['title']}' | Duration: {dur:.1f}s | Score: {c['virality_score']}")
        print(f"    Hook: '{c['hook']}'")
        print(f"    Transcript ending: '...{c['full_transcript'][-60:]}'")

        # 1. Complete sentence check: Must end on clean punctuation
        assert c["full_transcript"].strip()[-1] in [".", "!", "?"], "Clip must end on complete punctuation!"

        # 2. Duration check: Must satisfy min_seconds and max_seconds
        assert dur >= 60.0, f"Clip duration {dur:.1f}s must be >= 60.0s"
        assert dur <= 180.0, f"Clip duration {dur:.1f}s must be <= 180.0s"

        if 60.0 <= dur <= 95.0:
            sweet_spot_count += 1
        elif dur > 95.0:
            long_count += 1

    print(f"\n  -> Sweet-spot clips (60-95s): {sweet_spot_count}")
    print(f"  -> Extended complete long clips: {long_count}")
    assert sweet_spot_count >= 1, "AI must focus primarily on 60-90s clips"
    print("  -> Passed Test 1: Complete sentences and 60-90s focus verified!")

    # Case 2: User selects min 70s, max 300s
    print("\n[Test 2] User selects min_seconds = 70.0, max_seconds = 300.0:")
    clips_300 = detector.find_viral_clips(
        segments=segments,
        min_seconds=70.0,
        max_seconds=300.0,
        top_k=4,
        clip_mode="highlights"
    )
    assert len(clips_300) >= 2
    for i, c in enumerate(clips_300, 1):
        dur = c["duration"]
        print(f"  Clip {i}: Title: '{c['title']}' | Duration: {dur:.1f}s | Score: {c['virality_score']}")
        assert c["full_transcript"].strip()[-1] in [".", "!", "?"]
        assert dur >= 70.0, f"Duration {dur:.1f}s must be >= 70.0s"
        assert dur <= 300.0, f"Duration {dur:.1f}s must be <= 300.0s"

    print("  -> Passed Test 2: Extended 70-300s range verified!")

if __name__ == "__main__":
    test_sweet_spot_and_long_clips()
    print("\nALL DURATION & SENTENCE ALIGNMENT TESTS PASSED! 🚀")
