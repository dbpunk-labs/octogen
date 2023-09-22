FROM ubuntu
RUN apt update
RUN apt install -y python3 python3-pip
RUN pip install -U octopus_agent octopus_kernel hapless
ADD server /bin/
ADD start_all.sh /bin/
