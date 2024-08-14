FROM public.ecr.aws/docker/library/python:3.11.9-bookworm AS builder

RUN apt update && apt install -y gcc binutils libc-dev scons patchelf

WORKDIR /ssm-diff

COPY . .

RUN pip install -r requirements.txt pyinstaller staticx && \
  pyinstaller --clean -y --onefile ssm-diff && \
  staticx /ssm-diff/dist/ssm-diff /ssm-diff-static

FROM gcr.io/distroless/static-debian12:latest

COPY --from=builder /ssm-diff-static /ssm-diff

ENTRYPOINT ["/ssm-diff"]