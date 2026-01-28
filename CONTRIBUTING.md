# Contributing

## Getting Involved

We welcome contributions and are happy to discuss ideas, answer questions, and help you get started.

**Before opening a pull request**, please open an issue or start a discussion with the maintainers. This helps us:
- Ensure the change aligns with the project's direction
- Avoid duplicate or conflicting work
- Provide guidance on implementation approach

We're friendly and responsive—don't hesitate to reach out!

## Development

We ask you to write well covered unit tests with your changes and please make sure you use `black` and `flake8` to lint your code before making a PR. There are CI checks that will fail otherwise.

Linting and tests will run on python [3.9. 3.10 and 3.11](https://github.com/spotify/confidence-sdk-python/blob/nicklasl-patch-1/.github/workflows/pull-requests.yaml#L22).

We require pull request titles to follow the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/) and we also encourage individual commits to adher to that.

We use "squash merge" and any merge PR title will show up in the changelog based on the title.

Run the following if you need to regenerate the telemetry protobuf code:

```
./generate_proto.py
```