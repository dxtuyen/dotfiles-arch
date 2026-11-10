#!/usr/bin/env bash
# Translate the selection, falling back to the clipboard and Google Translate.
set -u

mode="${1:-vi-en}"
FALLBACK_GT=0

# Replace the previous notification with the latest result.
NTF_ID_FILE="${XDG_RUNTIME_DIR:-/tmp}/quick-lang-notify-id"
ntf() {
  old_id="$(cat "$NTF_ID_FILE" 2>/dev/null || true)"
  if [ -n "$old_id" ]; then
    makoctl dismiss -n "$old_id" 2>/dev/null || true
    sleep 0.1
  fi
  printf %s "$(notify-send -a quick-lang -p "$@")" > "$NTF_ID_FILE"
}

# Prefer the primary selection, then the clipboard.
text="$(wl-paste -p 2>/dev/null || true)"
[ -n "${text//[[:space:]]/}" ] || text="$(wl-paste 2>/dev/null || true)"
[ -n "${text//[[:space:]]/}" ] || {
  ntf "Quick Lang" "No text is selected or copied."
  exit 1
}

# An optional leading tag sets the writing context.
CTX_LABEL=""
CTX_RULE="Infer the domain and register from the text itself, then write the way an educated native speaker in that domain would naturally write."
if [[ $text =~ ^\[[[:space:]]*([A-Za-z]+)[[:space:]]*\] ]]; then
  tag="${BASH_REMATCH[1],,}"
  text="${text#*\]}"
  text="${text#"${text%%[![:space:]]*}"}"
  case "$tag" in
    phi) CTX_LABEL="phi"; CTX_RULE="Register: philosophical writing. Use precise abstract terminology, preserve hedging (perhaps, seems, may), and phrase it the way a careful philosopher would." ;;
    sci) CTX_LABEL="sci"; CTX_RULE="Register: academic/scientific writing. Formal and precise, with standard scientific hedging (suggest, indicate) and academic conventions." ;;
    lit) CTX_LABEL="lit"; CTX_RULE="Register: literary prose. Preserve imagery, voice, rhythm and figurative language; favor evocative, idiomatic phrasing over literal accuracy." ;;
    cas) CTX_LABEL="cas"; CTX_RULE="Register: casual natural conversation, the way a native speaker chats informally." ;;
    *)   CTX_LABEL="$tag"; CTX_RULE="Domain: $tag. Write it the way an expert in this field would naturally express the idea." ;;
  esac
fi

# Select the prompt for the requested translation mode.
case "$mode" in
  vi-en)
    rule="Convert the text below into polished, natural English. The text may be entirely Vietnamese (with or without diacritics), entirely English, or a mix of both. If it contains any Vietnamese, translate it and render the whole meaning as one coherent English text, integrating any already-English parts naturally. If it is entirely English, proofread it: when it is already correct and natural, output it EXACTLY unchanged; when it has real errors (grammar, word choice, collocation), output only the corrected text. $CTX_RULE Preserve the full meaning and tone of the original. Keep proper nouns and technical terms. Output ONLY the resulting English text, with no explanations or notes."
    gt_tl="en" ;;
  en-vi)
    rule="Convert the text below into natural Vietnamese with correct diacritics. The text may be entirely English, entirely Vietnamese, or a mix of both; render the whole meaning as one coherent Vietnamese text, integrating all parts naturally. $CTX_RULE Preserve the full meaning and tone of the original. Keep proper nouns and technical terms. Output ONLY the resulting Vietnamese text, with no explanations or notes."
    gt_tl="vi" ;;
  fix)
    rule="The text below is English written by a learner. Proofread it. If it is already correct and natural, output it EXACTLY unchanged. If it has real errors (grammar, word choice, collocation, unnatural phrasing), output only the corrected version, changing as little as possible. $CTX_RULE Preserve the author's meaning and voice. Keep proper nouns and technical terms. Output ONLY the resulting text, with no explanations or notes."
    gt_tl="" ;;
  *) ntf "Quick Lang" "Invalid mode: $mode (use vi-en, en-vi, or fix)"; exit 1 ;;
esac

# Retry network and server errors, but not quota errors.
translate_ai() {
  # Use Flash Lite for translation and Flash for proofreading.
  case "$mode" in
    vi-en|en-vi) MODEL="gemini-flash-lite-latest" ;;
    *)           MODEL="gemini-flash-latest" ;;
  esac

  API_KEY_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/quick-lang/api.key"
  API_KEY="$(cat "$API_KEY_FILE" 2>/dev/null | tr -d '[:space:]' || true)"
  if [ -z "$API_KEY" ]; then
    ntf -u critical "Quick Lang" "API key missing. Add it to ~/.config/quick-lang/api.key."
    exit 1
  fi

  prompt="$(printf '%s\n\nText:\n%s' "$rule" "$text")"
  resp_file="${XDG_RUNTIME_DIR:-/tmp}/quick-lang-resp.$$"
  http_code=""
  for attempt in 1 2 3; do
    http_code="$(timeout 40 curl -sS \
      --connect-timeout 5 --max-time 35 \
      -H "Content-Type: application/json" \
      -H "x-goog-api-key: $API_KEY" \
      -d "$(jq -n --arg p "$prompt" '{contents:[{parts:[{text:$p}]}], generationConfig:{temperature:0.2}}')" \
      -o "$resp_file" -w '%{http_code}' \
      "https://generativelanguage.googleapis.com/v1beta/models/$MODEL:generateContent" 2>/dev/null || true)"
    case "$http_code" in
      000|"") [ "$attempt" -lt 3 ] && sleep 1; continue ;;  # Retry network errors.
      5*)     [ "$attempt" -lt 3 ] && sleep 1; continue ;;  # Retry server errors.
    esac
    break  # Handle successful and client-error responses below.
  done
  response="$(cat "$resp_file" 2>/dev/null || true)"
  rm -f "$resp_file"

  result="$(printf '%s' "$response" | jq -r '.candidates[0].content.parts[0].text // empty' 2>/dev/null || true)"
  # Strip Markdown code fences if present.
  result="$(printf '%s' "$result" | sed -e 's/^```[a-zA-Z]*//' -e 's/```$//' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

  if [ -z "${result//[[:space:]]/}" ]; then
    # Fall back to Google Translate on translation quota errors.
    if [ "$http_code" = 429 ] && [ -n "$gt_tl" ]; then
      FALLBACK_GT=1
      return
    fi
    case "$http_code" in
      200)          msg="The API returned an empty response. Try again." ;;
      429)          msg="Gemini quota exceeded (HTTP 429). Wait a minute and try again." ;;
      400|401|403)  msg="The API key is invalid or was rejected (HTTP ${http_code})." ;;
      5*)           msg="Google API error (HTTP ${http_code}). Try again later." ;;
      *)            msg="Could not reach the Google API. Check your network and try again." ;;
    esac
    ntf -u critical "Quick Lang" "$msg"
    exit 1
  fi
}

# Use Google Translate as a keyless fallback when Gemini quota is exhausted.
translate_gt() {
  q="$(jq -rn --arg q "$text" '$q|@uri')"
  result=""
  for attempt in 1 2; do
    response="$(curl -sS --connect-timeout 5 --max-time 15 \
      -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36' \
      "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=$gt_tl&q=$q" 2>/dev/null || true)"
    result="$(printf '%s' "$response" | jq -r 'if (.[0]|type)=="string" then map(select(type=="string"))|join("") else map(.[0] // "")|join("") end' 2>/dev/null || true)"
    [ -n "${result//[[:space:]]/}" ] && break
    sleep 1
  done

  if [ -z "${result//[[:space:]]/}" ]; then
    ntf -u critical "Quick Lang · GT" "Translation failed. Check your network connection."
    exit 1
  fi
}

translate_ai

if [ "${FALLBACK_GT:-0}" = 1 ]; then
  ntf "Quick Lang · GT" "Gemini quota exceeded; using Google Translate."
  translate_gt
fi

printf %s "$result" | wl-copy

# Indicate whether proofreading changed the text.
case "$mode" in
  vi-en)
    if [ "$result" = "$text" ]; then title="✓ EN unchanged"; else title="→ EN"; fi ;;
  fix)
    if [ "$result" = "$text" ]; then title="✓ EN unchanged"; else title="✍️ EN corrected"; fi ;;
  en-vi) title="→ VI" ;;
esac
[ -n "$CTX_LABEL" ] && title="$title · $CTX_LABEL"

ntf "$title" "$result"
