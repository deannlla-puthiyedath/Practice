# Della Antony — portfolio: deploy notes

**What to upload:** only the `site/` folder (or the zip: unzip it, drag the folder it contains).
`sources/` holds the original photos and clips; they still carry phone/GPS metadata, so never upload that folder.

## 1 · Netlify Drop (about 2 minutes, free)
1. Go to **app.netlify.com/drop** and sign in (a free account keeps the site permanently).
2. Drag the **`site`** folder (or the unzipped folder) onto the page.
3. Netlify gives you a link like `https://random-name-123.netlify.app`. Open it on your phone and check it.
4. Optional: *Site configuration → Change site name* → something short, e.g. `della-antony`.

## 2 · Fix the link preview (WhatsApp / email) — 1 line
Preview crawlers need the full address of the preview image.
In `site/index.html`, find `https://YOUR-SITE.netlify.app/assets/og/og.jpg` and put your real address in its place, then drag the folder onto Netlify again (same site → "Deploys" → drop the folder).
Or send the link to Claude and ask for it to be done. WhatsApp caches previews: if you test before fixing this, share a link with `?v=2` on the end to see the new one.

## 3 · Optional: `actor.dellaantony.com`
1. Netlify → your site → *Domain management → Add a domain* → `actor.dellaantony.com`.
2. At wherever `dellaantony.com` DNS is managed, add a **CNAME** record: name `actor`, value `your-site-name.netlify.app`.
3. Wait a few minutes; Netlify issues the HTTPS certificate on its own.
Then update the preview address from step 2 to `https://actor.dellaantony.com/assets/og/og.jpg`.

## Privacy: what is and isn't protected
- Search engines are told to stay away (`noindex`, `robots.txt`, and a `noindex` header Netlify applies from `_headers`). The link is unlisted, **not password-protected**: anyone who has it can open it.
- No analytics, cookies or trackers. Fonts are served from the site itself. The only third party is Google Drive, and only when someone taps play on a Drive clip.
- No phone number or home address anywhere. Photos have had all metadata (including the GPS tag on `Toronto.JPG`) removed.
- `hello@dellaantony.com` must be a working inbox: it is the only way anyone can reach you from the page.

## Still to add
Clips **02 Tamil monologue** and **03 British accent** (both in your brief) were not in the Drive folders shared with Claude.
Easiest: share each as "Anyone with the link" and send the links; they slot into the Voices row in the right order, and the line "Five takes. Four languages. One voice." fills itself in.
Durations for the Tamil intro and the song are not shown, because those two files were too large for Claude to read. Send the lengths (e.g. `0:41`) if you want them on the slates.

## Folder map
```
site/       ← the website (index.html, style.css, main.js, fonts/, assets/, robots.txt, _headers)
sources/    ← originals (not uploaded)
tools/      ← process-assets.sh rebuilds every image/poster; make-og.js rebuilds the preview image
```
