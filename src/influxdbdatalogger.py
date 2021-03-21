#!/usr/bin/python3
import logging
import sys
import getopt
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

###############################################################
# influxdbdatalogger.py script can be run from command line   #
# or can be started as systemd service or Raspberry Pi        #
# Main tasks of the script are:                               #
#     - read environment data received as mqtt message        #
#     - store received data in InfluxDB database              #
#                          <C> Andrzej Mazur, 17/03/2021      #
###############################################################


##########################
#MQTT Connection Settings#
##########################
#Quality of Service Level for MQTT transfer, supported values 0 and 1
mqtt_qos=1
#Broker address - Change this line!
#Test Broker address: test.mosquitto.org
mqtt_broker_address="test.mosquitto.org"
#mqtt_broker_address="localhost"
#Brokers TCP Port number
mqtt_broker_port=1883
#Connection keep alive interval in sec
mqtt_keep_alive=60
#Topic on which measurement record will be published
mqtt_topic="47e0g1/headlesspi/climdata"

##############################
#InfluxDB Connection Settings#
##############################
influxdb_user = "climatedata_probe"
influxdb_pass = "probepi"
influxdb_dbname   = "climatedata"
influxdb_measurementname = "climatemeasurements"
influxdb_host = "127.0.0.1"
influxdb_port = 8086


debug = False

def cmd_usage():
  print ('Usage: '+sys.argv[0]+' {[-d | --debug debug] [-h | --host host] [-q | --qos QoS] [-t | --topic topic] [-a | --bfe280addr bfe280 address]')
  exit (1)

try:
    options, arguments = getopt.getopt(sys.argv[1:], 'dh:q:t:', ['debug', 
                                                             'host=',
                                                             'qos=',
                                                             'topic=',   
                                                             ])
 #   if not options:
 #     print ('No options supplied')
 #     usage()
      
except getopt.GetoptError as err:
    print(str(err))
    cmd_usage()
    sys.exit(1)

for opt, arg in options:
    if opt in ('-d', '--debug'):
        debug = True
    elif opt in ('-h', '--host'):
        mqtt_broker_address = arg
    elif opt in ('-q', '--qos'):
         mqtt_qos = int(arg)
    elif opt in ('-t', '--topic'):
         mqtt_topic = arg


#configure logger module
#levels: DEBUG,INFO,WARNING,ERROR,CRITICAL
if debug==True:
    logging.basicConfig(level=logging.DEBUG,format='%(asctime)s:%(filename)s:%(lineno)s:%(levelname)s:%(message)s')
else:
    logging.basicConfig(level=logging.INFO,format='%(asctime)s:%(filename)s:%(lineno)s:%(levelname)s:%(message)s')
    
    
if mqtt_qos != 0 and mqtt_qos != 1:
    mqtt_qos = 1
    logging.warning('Provided MQTT QoS value is not supported. Default QoS=1 is used...')

def mqtt_on_connect(mqtt_client, userdata, flags, rc):
    if rc==0:
        mqtt.Client.connected_flag=True #flag set
        logging.debug('Received:MQTT_CONNACK(rc=%i)',rc)
        logging.debug('Connection to MQTT Broker established!')
        #Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        (result,mid)=mqtt_client.subscribe(mqtt_topic,mqtt_qos)
        logging.debug('Sent:MQTT_SUBSCRIBE(mid=%i, topic:%s, QoS=%i, rc=%i)',mid,mqtt_topic, mqtt_qos, result)
    else:
        logging.debug('Received:MQTT_CONNACK(rc=%i)',rc)
        logging.debug('Connection establishment to MQTT Broker failed!')
        
def mqtt_on_disconnect(mqtt_client, userdata, rc):
    mqtt.Client.connected_flag=False #flag set
    if rc==0:
       logging.debug('Disconnection from MQTT Broker completed!')
    else:
        logging.error('Unexpected disconnection from MQTT Broker!')
        
def mqtt_on_message(mqtt_client, userdata, msg):
    logging.debug('Received:MQTT_PUBLISH(topic=%s, qos=%s, retain=%s, payload=%s)', msg.topic,msg.qos,msg.retain,msg.payload)
    mqtt_msg = json.loads(msg.payload)
    influxdb_store_data_sample(influxdb_host,influxdb_port,influxdb_user,influxdb_pass,influxdb_dbname,influxdb_measurementname, mqtt_msg)


    
def mqtt_on_subscribe(client,userdata,mid,granted_qos):
    logging.debug('Received:MQTT_SUBACK(mid=%i,negotiatedQoS=%i)',mid, granted_qos[0])
    logging.info('Client ready to receive messages!')

def influxdb_store_data_sample(dbhost,dbport,dbuser,dbpass,dbname,dbmeasurement,data):
    #build database record from received json string
    logging.info('Measurement to be added to "%s" meas. in "%s" db:',dbmeasurement,dbname)
    logging.info("   sensor id: %s", str(data['bme280id']))
    logging.info('   timestamp: %s',list(data.keys())[1])
    logging.info('   temperature: %f%s',float(data[list(data.keys())[1]]['temperature']['value']),data[list(data.keys())[1]]['temperature']['unit'])
    logging.info('   pressure: %f%s',float(data[list(data.keys())[1]]['pressure']['value']),data[list(data.keys())[1]]['pressure']['unit'])
    logging.info('   humidity: %f%s',float(data[list(data.keys())[1]]['humidity']['value']),data[list(data.keys())[1]]['humidity']['unit'])
 
    # connect to influx
    # it is possible to connect once and in this function call just write to database, but it is less reliable method
    ifclient = InfluxDBClient(dbhost,dbport,dbuser,dbpass,dbname)
    
    # write the measurement taken by bme280
    # format the data as a single measurement for influx
    dbrecord = [
        {
            "measurement": dbmeasurement,
            "tags": {
                "sensor_id":str(data['bme280id']),
                "location": mqtt_topic.split("/")[0]
                },
            "time": list(data.keys())[1],
            "fields": {
                "temperature_C": float(data[list(data.keys())[1]]['temperature']['value']),
                "pressure_hPa": float(data[list(data.keys())[1]]['pressure']['value']),
                "humidity_rH": float(data[list(data.keys())[1]]['humidity']['value'])
            }
        }
    ]

    ifclient.write_points(dbrecord)
    
    # write the measurement taken by bme280
    # format the data as a single measurement for influx
    dbrecord = [
        {
            "measurement": dbmeasurement,
            "tags": {
                "sensor_id":str(data['ds18b2id']),
                "location": mqtt_topic.split("/")[0]
                },
            "time": list(data.keys())[3],
            "fields": {
                "temperature_C": float(data[list(data.keys())[3]]['temperature']['value'])
            }
        }
    ]
    
    ifclient.write_points(dbrecord)

    
#create connection state flag in class
mqtt.Client.connected_flag=False

#create mqtt client instance
mqtt_client = mqtt.Client()

#bind callback functions 
mqtt_client.on_connect=mqtt_on_connect
mqtt_client.on_disconnect=mqtt_on_disconnect
mqtt_client.on_message=mqtt_on_message
mqtt_client.on_subscribe=mqtt_on_subscribe

logging.debug('Sent:MQTT_CONNECT:(IP:%s,TCP Port:%s,Topic:%s,QoS:%i,KeepAlive:%i)',mqtt_broker_address, mqtt_broker_port, mqtt_topic, mqtt_qos, mqtt_keep_alive)

#connect to MQTT Broker
try:
    mqtt_client.connect(mqtt_broker_address,mqtt_broker_port,mqtt_keep_alive)
except:
    logging.error('Connection establishment failed due to: %s, exiting the program...', sys.exc_info()[1])
    exit(1) #Should quit or raise flag to quit or retry (not implemented)

#start network loop and disconnect from MQTT Broker
try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    logging.info('Exiting the program, ctrl+C pressed...')
    logging.debug('Sent:MQTT_DISCONNECT')
    logging.debug('Disconnecting from MQTT Broker')
    mqtt_client.disconnect();
