# QtPass city

The tests of [QtPass](https://qtpass.org) as a city at night. Every test
suite is a glass tower and every test a window that lights up green the
moment the test lands on main. Releases are fireworks, CI workflows are
searchlights sweeping the sky, and the commits are traffic: light snakes on
the streets, as busy as the project was that week, coloured by what kind of
commit each carries (translations, fixes, features, tests, CI, docs, tidying).

The story is in the data: the first test arrived on 13 December 2016 ("LOL
wut, also how do I link .."), there were three for eight years, and then in
2026 the city went up: 140 tests in a week in March, another 140 in four days
in May, 526 in one week in September, 1,256 tests in 37 suites by November.
Time in the film follows those beats, not the calendar.

A sibling of [qtpass-strata](https://github.com/annejan/qtpass-strata), which
tells the same history as a canyon wall.

## Files

- `count_tests.py`: counts the Qt Test functions per suite at every commit on
  main that touched `tests/` (and weekly), plus CI workflows, release tags and
  every commit with its kind, into `data/`
- `layout.py`: where the towers and streets are
- `traffic.py`: the light snakes, simulated once for the whole film
- `timeline.py`: the one clock (which date it is at every frame, tests per
  suite, camera path, title times) shared by the scene, the cards and the sound
- `build_scene.py`: builds the city in Blender and renders it, setting every
  tower, window, beam and firework for each frame
- `cards.py`: Lato title cards with the QtPass logo, as transparent PNGs
- `audio.py`: the soundtrack (crickets, city hum, one blip per test, fireworks,
  a riser into September), generated with numpy and scipy
- `finish.sh`: bloom, vignette, grain, fades, titles and sound into an MP4
- `preview.py`: a flat matplotlib storyboard of the timeline, before any 3D
- `topview.py`: the town flat from above with its traffic, as a quick video

## Pipeline

```sh
python3 count_tests.py ~/Projects/QtPass bb0fad7a9     # -> data/
python3 preview.py                                     # -> preview.png
python3 topview.py                                     # -> topview.mp4
blender -b --factory-startup -P build_scene.py -- --stills 229,1057,1873 --pct 25
./render_chunks.sh 1 2040 25 16 frames                 # low-res, resumes after a crash
python3 audio.py audio.wav
./finish.sh renders/frames qtpass-city.mp4
CARDS_LANG=uk ./finish.sh renders/frames qtpass-city-uk.mp4   # Ukrainian titles
```

The titles are laid over the rendered frames by `finish.sh`, so another
language costs one more encode, not a render: add `cards/<lang>.json` with
the words for each card (see `cards/uk.json`).

2040 frames at 24 fps (85 s), 3840x1608 (2.39:1) at 100 %. A test is a
`void name();` under `private slots:` in a `tst_*.cpp` or `tst_*.h`, minus
`init`, `cleanup`, `initTestCase`, `cleanupTestCase` and `_data` providers;
for `tst_util` that matches what the binary's `-functions` lists.

Needs Blender 5.1, Python 3 with numpy, scipy, Pillow and matplotlib, ffmpeg,
and the Lato fonts in `~/.local/share/fonts/Lato/`.
