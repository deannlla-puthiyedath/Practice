"""Reel 6 quote pool: 'being in the now'. Every line is copied from the manuscript.
Each quote is a list of cut-letter tiles (8 words or fewer each). Tiles joined with a space must equal the book text.
Check:  python3 verify_quotes.py <path to decoded book text>"""

GROUPS = [
 ("A. Come back, be here (hooks)", [
  ("A1", "Ch 6", ["Nope. You are still not here."], "Hook. Scores 87 STRONG. The line before it in the book is 'Alright now, for real, come back.'"),
  ("A2", "Ch 6", ["Alright now, for real, come back.", "Nope. You are still not here."], "Same moment with the line before it. Scores lower alone, reads softer."),
  ("A3", "Ch 6", ["Focus. on. this. word."], "Funny and meta. Needs a tile with the word 'Now' next to it."),
  ("A4", "Ch 3", ["Think Now.", "Dream after."], "Sock's line. In Reel 5's caption draft, never on screen."),
  ("A5", "Ch 4", ["Now, now", "Don’t panic.", "You WILL wake up."], "Gentle, for the hurried beat."),
  ("A6", "Ch 4", ["Now, Now,", "I ask you what Sock asked me.", "What do we do when we fall?", "We wake up."], ""),
  ("A7", "Ch 4", ["Now be quiet, I tell you.", "Because it’s time."], "Echoes the book's 'Is it time?'"),
  ("A8", "Ch 4", ["Then, listen, you say.", "I Am.", "Why tell me what I already know?"], ""),
  ("A9", "Ch 4", ["Oh, you know.", "You know plenty.", "You just need to Wake Up", "To what you know."], ""),
 ]),
 ("B. Breath, body, roots", [
  ("B1", "Ch 6", ["So take a deep breath.", "Like you’re not afraid to feel.", "The kind that goes all the way", "to your toes and root", "yourself like a tree."], "Consecutive in the book. Best spine for the middle of the reel."),
  ("B2", "Ch 6", ["This will get easier", "as it becomes more meaningful.", "It will become more meaningful", "as you practice more.", "You will practice more", "as you find the easiness in it."], "Comes right after B1 in the book. A loop: each line hands to the next."),
  ("B3", "Ch 6", ["I could breathe deep", "like I imagine a tree does."], ""),
  ("B4", "Ch 6", ["From the leaves at the tip", "of its body deep down all the way", "to its roots and like a whisper,", "pass it to the ground beneath."], "Follows B3. A breath travelling from leaves to roots."),
  ("B5", "Ch 6", ["And I was a tree", "in it and on it.", "With roots and stuff."], "Light and funny."),
  ("B6", "Ch 6", ["And the outside of my head,", "turns out, was neither Heaven or Hell;", "but a planet."], ""),
  ("B7", "Ch 6", ["I was learning to become", "both a tree and the planet", "at the same time."], ""),
  ("B8", "Ch 6", ["For the first time in my", "anxious, unfulfilling life,", "I wasn’t scared anymore."], "Next line in the book is 'I was there and then.' (probably 'here and now'; check with Della before using)"),
  ("B9", "Ch 6", ["I was alive.", "I was in my body."], ""),
  ("B10", "Ch 6", ["Or that I would become the calm."], ""),
  ("B11", "Ch 5", ["I was alive.", "I had a presence.", "A strong one at that."], ""),
  ("B12", "Ch 5", ["That’s why children command the room.", "Not because they need help.", "Not because they bring joy.", "They are alive."], "Stop at 'They are alive.' (the book adds 'And we are not.', which is heavier)."),
  ("B13", "Ch 9", ["And we sit still", "as we dive into the insides of us."], ""),
  ("B14", "Ch 9", ["The staircase to heaven", "is within us."], ""),
  ("B15", "Ch 9", ["I have just taught you how to meditate."], "Funny. Good for after the breath."),
 ]),
 ("C. No hurry", [
  ("C1", "Ch 13", ["We will arrive when we arrive."], "Calm closing line."),
  ("C2", "Ch 9", ["Rest, my child,", "for as long as you want.", "There is no hurry.", "There is no competition."], "Mum's voice. Good for the courtyard."),
  ("C3", "Ch 10", ["That’s why I tell you,", "there is no shame in sleeping", "for as long as you need."], ""),
  ("C4", "Ch 10", ["I woke up too fast."], "Short and honest."),
  ("C5", "Ch 6", ["I hate the breaks in nature", "and the impermanence of time", "and the non-linearity of life", "as much as you do."], ""),
  ("C6", "Ch 10", ["By that, blame and guilt and regret", "are ego tools to keep you", "stuck on a loop and what failures", "really are, is that they are god-designed."], "The past and future as a loop. Longest line here."),
  ("C7", "Ch 12", ["Time will die then.", "The last of our hearts will open."], "Poetic: time stopping."),
  ("C8", "Ch 8", ["Yes.", "Now now, it’s been a long day."], "Evening line. Book then says 'Go sleep.' (leave it out)."),
 ]),
 ("D. Sun, sea, dawn (the painting)", [
  ("D1", "Ch 2", ["Haven’t we all waited so long", "for the sun and forgotten about it", "right before the dawn?"], "Fits a sunset. Reel 3 listed it as a spare, never used."),
  ("D2", "Ch 2", ["He had an ocean in his eyes", "that only the seekers would find."], ""),
  ("D3", "Ch 12", ["And who ever wins,", "love or darkness,", "it will snow under the sun."], "Odd and lovely."),
 ]),
 ("E. What I already have (the farmer)", [
  ("E1", "Ch 14", ["I am a farmer.", "I water the plants I have."], "Present moment as a plain act."),
  ("E2", "Ch 14", ["I am a farmer.", "I don’t judge what I am given."], ""),
  ("E3", "Ch 14", ["Like the farmer,", "he pursued wisdom", "and he kept his world simple."], ""),
  ("E4", "Ch 14", ["He only sought just enough tools", "to grow the plants that grew", "in the land he was given."], ""),
  ("E5", "Ch 13", ["All along we set sail to find ourselves.", "The greatest joy in the world", "has always been meeting ourselves."], "Reel 3 listed it as a spare, never used."),
 ]),
 ("F. Where the mind goes instead (the 'before' beat)", [
  ("F1", "Ch 6", ["I didn’t hear the clause", "that came after the promise", "because the flaw of humans", "was that we are", "easily distracted."], "The book breaks it as 'we / are / easily / distracted.'"),
  ("F2", "Ch 6", ["The promise had the life", "that dwelled in the whole of my body", "retreat back into my head."], ""),
  ("F3", "Ch 6", ["I could no longer feel my body.", "I was outside of it."], ""),
  ("F4", "Ch 5", ["We are addicted to escapes", "and our heart flutters,", "we soar high into our imaginations", "till something brings us back", "to the reality."], ""),
  ("F5", "Ch 7", ["Maybe distractions aren’t", "the worst thing in the world."], "Kind. Good to follow F1."),
  ("F6", "Ch 1", ["But we have to be brave because", "what world to live for", "if not the real one?"], ""),
 ]),
 ("G. Closers", [
  ("G1", "Ch 9", ["You will then open your eyes", "to find the joy behind the pain.", "And the real life would", "finally begin for you."], ""),
  ("G2", "Ch 8", ["You have to live consciously."], "The next line is 'Only then you would know if the scales are being balanced.'"),
 ]),
]

USED = [
 "We bury secrets in us and believe we all hold the same ones. (Reel 3)",
 "But you can’t drown the oceans or hide the cloak of invisibility. (Reel 3)",
 "We receive the grace of acceptance. With acceptance, comes a calm. (Reel 3)",
 "We listen with a stillness. (Reel 3)",
 "Reel 4 (Reverie): 'What if I told you everything that you have built...'",
 "Reel 5: the whole Love and Truth chapter lines (Ch 3).",
]
