FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3 python3-pip
RUN pip install -U og_proto og_sdk og_agent og_kernel hapless
RUN useradd -ms /bin/bash octogen
ADD server /bin/
ADD start_all.sh /bin/
ADD start_kernel.sh /bin/
ADD add_endpoint.sh /bin/
