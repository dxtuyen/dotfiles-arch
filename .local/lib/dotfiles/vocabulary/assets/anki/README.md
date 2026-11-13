# Anki card templates and styles

## Longman vocabulary cards

GoldenDict-ng sends vocabulary to the `Longman` note type using `Word`,
`selected_text`, and `marked_sentence`. The Longman templates provide a reading
column, light and dark colors, audio replay styling, and a link back to GoldenDict.
The answer shows lookup context only when it contains more than the headword.
The back template automatically presents one English meaning, one example, and
one phrase from the selected Longman text, with IPA and part of speech when
available. It omits navigation labels and additional senses from the short view;
**More details** expands the complete imported text. Audio remains visible once.
This runs inside the template, so new imports automatically use the same layout
without an additional service, port, API, or manual editing. The template and its
script travel with Anki Sync.

The display script also hides object-replacement glyphs left by dictionary icons.
It does not translate, invent missing examples, or change stored note fields.
Hand-formatted paragraph/list/table content retains its layout; unrecognized
selections remain visible in full.

The installer links `anki-longman-setup` and configures GoldenDict's connection,
field mapping, audio setting, and disabled online/demo sources. Dictionary paths
start empty on a new machine; add your own later in GoldenDict. It defers
GoldenDict edits if the app is running. AnkiConnect still needs to be installed
once in Anki; dictionary files and AnkiWeb login are personal data, kept outside
the repository.

On another machine, sync the existing AnkiWeb collection first; the note type,
templates, review history, and media travel with the collection. Quit GoldenDict
using its tray menu, open Anki with AnkiConnect enabled, close the card template
editor, and run:

```bash
anki-longman-setup
anki-longman-setup --check
```

The command finishes GoldenDict setup and verifies/applies the repository's
Longman templates. It refuses to create a missing note type/deck by default so
you can sync your existing collection first. For a genuinely new collection with
no existing vocabulary to restore, use `anki-longman-setup --initialize`; this
creates the note type and empty `LongMan` deck, but no notes.

The complete migration steps, including the AnkiConnect installation code and a
connection check, are in the [vocabulary runbook](../../../../docs/vocabulary.md).

To update only Anki's templates from a checkout, without changing GoldenDict:

```bash
python3 lib/vocabulary/scripts/apply-longman.py
```

The Python command updates the existing single card template and CSS of `Longman`.
It verifies the result without creating notes, changing fields, or touching
review scheduling. It writes no backup files. Other note types retain their
existing templates and styles.

To edit the design, update [`longman-front.html`](longman-front.html),
[`longman-back.html`](longman-back.html), or [`longman.css`](longman.css), then run
the command again. You can also paste these files into Anki's Front Template,
Back Template, and Styling tabs under **Tools → Manage Note Types → Longman → Cards**.

For new vocabulary, look up a word in GoldenDict-ng and click **Send Current
Article to Anki** (or press **Ctrl+Shift+N**) without selecting text. The short view uses
the first ordinary entry and its first meaning/example; it cannot infer which
sense you encountered in your reading. Selecting a later sense is optional.
`--check` reads configuration/API only, returns nonzero on mismatch, and works
while GoldenDict is running; it never creates notes or updates templates.
IPA and part of speech can only be shown when present in the selection. The
built-in `Sentence` mapping still sends the lookup string; the example in the
short view is extracted from `selected_text`, not from that lookup field.

## Yanki stylesheet

[`yanki-dark.css`](yanki-dark.css) styles Yanki-managed Anki note types. It provides a Markdown-friendly layout, bordered tables, blockquotes, GitHub-style alerts, links, inline code, highlights, and responsive images/video. It keeps formulas readable and applies dark colors to Shiki code blocks in Anki Night Mode. Its colors are maintained independently of the desktop palette.

Inline math (`$...$`) stays in the text flow at the surrounding font size, even
when it is the only formula in a paragraph. Use display math (`$$...$$`) for
centered equations. Both forms scroll horizontally when wider than their container
and retain their font size on narrow screens. Inline formulas can move as a whole
to the next line; short formulas keep their baseline alignment with the text.

For consistent parsing between Obsidian and Yanki, put display-math fences on
separate lines. `$$...$$` on one line can become inline math in Yanki. Inside a
list, indent both the formula and the closing fence to the list item's content
column (two spaces after a `- ` marker):

```markdown
- $$
  j_D = \frac{i_D}{A} = \varepsilon_0 \frac{dE}{dt}
  $$

$\varepsilon_0$ : Permittivity of free space (F/m).
```

An unindented closing fence leaves the list and can start a new math block that
consumes the following explanation. CSS cannot repair this parsing error; fix
the Markdown and sync the note again.

The stylesheet formats HTML already generated by Yanki; it does not change source
Markdown or card templates. Obsidian callouts that Yanki renders as ordinary
blockquotes receive the blockquote style, without adding callout parsing or
collapsing behavior. Recognized alerts use one restrained accent color.

### Apply the stylesheet

1. Open Anki with AnkiConnect enabled.
2. Close any open Anki card editor.
3. Run the following command from the repository root:

```bash
npx --yes yanki style --css "$PWD/lib/vocabulary/assets/anki/yanki-dark.css"
```

The command updates the styling of Yanki-managed note types in the open collection. Other note types retain their existing styles.

See the [configuration notes](../../../../docs/README.md) for general usage and maintenance.
