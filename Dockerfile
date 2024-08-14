FROM public.ecr.aws/docker/library/python:3.11.9-alpine AS builder

RUN apk add --update gcc musl-dev binutils libc-dev

WORKDIR /ssm-diff

COPY . .

RUN pip install -r requirements.txt pyinstaller && \
  pyinstaller --clean -y --onefile ssm-diff

FROM gcr.io/distroless/base:debug

COPY --from=builder /ssm-diff/dist/ssm-diff /

#ENTRYPOINT ["/ssm-diff"]