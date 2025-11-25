# mopidy-alsamixer

[![Latest PyPI version](https://img.shields.io/pypi/v/mopidy-alsamixer)](https://pypi.org/p/mopidy-alsamixer)
[![CI build status](https://img.shields.io/github/actions/workflow/status/mopidy/mopidy-alsamixer/ci.yml)](https://github.com/mopidy/mopidy-alsamixer/actions/workflows/ci.yml)
[![Test coverage](https://img.shields.io/codecov/c/gh/mopidy/mopidy-alsamixer)](https://codecov.io/gh/mopidy/mopidy-alsamixer)

[Mopidy](https://mopidy.com) extension for ALSA volume control.


## Maintainer wanted

Mopidy-SoundCloud is currently kept on life support by the Mopidy core
developers. It is in need of a more dedicated maintainer.

If you want to be the maintainer of Mopidy-SoundCloud, please:

1.  Make 2-3 good pull requests improving any part of the project.

2.  Read and get familiar with all of the project's open issues.

3.  Send a pull request removing this section and adding yourself as the
    "Current maintainer" in the "Credits" section below. In the pull
    request description, please refer to the previous pull requests and
    state that you've familiarized yourself with the open issues.

    As a maintainer, you'll be given push access to the repo and the
    authority to make releases to PyPI when you see fit.


## Installation

Install by running:

```sh
python3 -m pip install mopidy-alsamixer
```

See https://mopidy.com/ext/alsamixer/ for alternative installation methods.


## Configuration

To use mopidy-alsamixer the `audio/mixer` configuration value must be set to
`alsamixer` in the Mopidy configuration file:

```ini
[audio]
mixer = alsamixer
```

The default mopidy-alsaMixer configuration will probably work for most use
cases. If not, the following configuration values are available:

- `alsamixer/device`: Which soundcard should be used, specified by its string
  alias. Defaults to `default`.

- `alsamixer/card`: Which soundcard should be used, specified by its index.
  Numbered from 0 and up. If specified, `alsamixer/device` is ignored.

- `alsamixer/control`: Which ALSA control should be used. Defaults to `Master`.
  Other typical values includes `PCM`. Run the command `amixer scontrols`
  to list available controls on your system.

- `alsamixer/min_volume` and `alsamixer/max_volume`: Map the Mopidy volume
  control range to a different range. Values are in the range 0-100. Use this
  if the default range (0-100) is too wide, resulting in a small usable range
  for Mopidy's volume control. For example try `min_volume = 30` and
  `max_volume = 70` to map Mopidy's volume control to the middle of ALSA's
  volume range.

- `alsamixer/volume_scale`: Either `linear`, `cubic`, or `log`. The
  cubic scale is the default as it is closer to how the human ear percieves
  volume, and matches the volume scale used in the `alsamixer` program.

Example `alsamixer` section from the Mopidy configuration file:

```ini
[alsamixer]
card = 1
control = PCM
min_volume = 0
max_volume = 100
volume_scale = cubic
```


## Project resources

- [Source code](https://github.com/mopidy/mopidy-alsamixer)
- [Issues](https://github.com/mopidy/mopidy-alsamixer/issues)
- [Releases](https://github.com/mopidy/mopidy-alsamixer/releases)


## Development

### Set up development environment

Clone the repo using, e.g. using [gh](https://cli.github.com/):

```sh
gh repo clone mopidy/mopidy-alsamixer
```

Enter the directory, and install dependencies using [uv](https://docs.astral.sh/uv/):

```sh
cd mopidy-alsamixer/
uv sync
```

### Running tests

To run all tests and linters in isolated environments, use
[tox](https://tox.wiki/):

```sh
tox
```

To only run tests, use [pytest](https://pytest.org/):

```sh
pytest
```

To format the code, use [ruff](https://docs.astral.sh/ruff/):

```sh
ruff format .
```

To check for lints with ruff, run:

```sh
ruff check .
```

To check for type errors, use [pyright](https://microsoft.github.io/pyright/):

```sh
pyright .
```

### Making a release

To make a release to PyPI, go to the project's [GitHub releases
page](https://github.com/mopidy/mopidy-alsamixer/releases)
and click the "Draft a new release" button.

In the "choose a tag" dropdown, select the tag you want to release or create a
new tag, e.g. `v0.1.0`. Add a title, e.g. `v0.1.0`, and a description of the changes.

Decide if the release is a pre-release (alpha, beta, or release candidate) or
should be marked as the latest release, and click "Publish release".

Once the release is created, the `release.yml` GitHub Action will automatically
build and publish the release to
[PyPI](https://pypi.org/project/mopidy-alsamixer/).


## Credits

- Original author: [Stein Magnus Jodal](https://github.com/mopidy)
- Current maintainer: None. Maintainer wanted, see section above.
- [Contributors](https://github.com/mopidy/mopidy-alsamixer/graphs/contributors)
