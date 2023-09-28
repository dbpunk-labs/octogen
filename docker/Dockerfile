FROM ubuntu
RUN apt update
RUN apt install -y python3 python3-pip
RUN pip install -U og_agent og_kernel hapless
ADD server /bin/
ADD start_all.sh /bin/
