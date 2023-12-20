# Use a Python runtime as a parent image
FROM python:3.9

# Set the version as a build argument (default to "v1.0" if not provided)
ARG VERSION=v1.0

# Set the timezone
ENV TZ=Europe/Berlin

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY backup.py .
COPY requirements.txt . 

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install rsync
RUN apt-get update && apt-get -y install rsync vim sudo

# Set environment variables
ENV BACKUP_DESTINATION=/backup

# Set SSH options
RUN echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config
RUN mkdir -p /root/.ssh
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa

# Set up cron job with environment variables
RUN apt-get update && apt-get -y install cron \
    && echo "0 0 * * * root /usr/local/bin/python3.9 /usr/src/app/backup.py" > /etc/cron.d/backup-cron \
    && chmod 0644 /etc/cron.d/backup-cron \
    && crontab /etc/cron.d/backup-cron \
    && service cron start

# Run backup.py when the container launches
CMD ["cron", "-f"]
