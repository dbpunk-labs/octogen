FROM ubuntu
RUN apt update
RUN apt install -y python3 python3-pip
RUN pip install -U octopus_agent octopus_kernel
ADD start_agent.sh /bin/
ADD start_kernel.sh /bin/
