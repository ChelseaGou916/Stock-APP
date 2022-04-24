FROM python:3.7.4

COPY . /352ass1

WORKDIR /352ass1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#Uncomment just the next 2  lines to run your application in Docker container
EXPOSE 8080
CMD python gxcServer3.py 8080

#Uncomment just the next line when you want to deploy your container on Heroku
#CMD python gxcServer3.py $PORT
