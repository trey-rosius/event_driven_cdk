# Designing Event Driven Architectures
## Building Modern Serverless API's with Python, CDK and GraphQL
> The World is Asynchronous..Dr Werner Vogels ReInvent 2022

The concept of `Event Driven Architectures(EDA)` is not new. As a matter of fact,it's been around for ages. But lately, it's been 
the talk of every tech clique. There's no way you can scroll through tech twitter without coming across a tweet concerning 
EDA. 
But what are EDA's and why is every organization adopting this architectural pattern ?

### Event Driven Architectures ?
Minimizing the degree of interdependence between different components of a system is the main aim of event driven architectures. 
The terms `loosely coupled` or `Decoupling` is generally used.
EDA's use events to coordinate communication between loosely coupled services.
But what are events ?

## Events
An event is a change in state, or an update, like an order added to the cart in a restaurant application . Events can either carry the state (the item purchased, its price, and a quantity) 
or events can be identifiers (a notification that a payment was successful or not).

EDA's are made up of 3 parts.
### Event Producers
This can be a mobile app or an ecommerce site

### Event Routers
This can be an event store

### Event Consumers
This can be a database, saas application, microservice etc

So an event producer publishes an event to the event router, the event router filters and pushes the event to consumers.
The event router abstracts the producer from the consumer by allowing them to communicate asynchronously.

## Why you should adopt EDA

- With services that scale on demand and fail independently, your application is bound to be reliable and resilient.
- Event routers coordinate events automatically between producers and consumers, so you no longer need to write code to handler that.
- Event-driven architectures are push-based, so everything happens on-demand as the event presents itself in the router. 
This way, you’re not paying for continuous polling to check for an event. 
- EDA's are responsive to the needs of customers as they expect systems to respond to events as they happen.
- EDA's are cost effective, allowing customers to pay only for the services they need, when they need them.

Now that we have a brief understanding of what EDA's are, let's go ahead and dive into the main topic for the blog post.

We'll use the concept of EDA's to design and build a modern serverless graphql api.

## Use Case
We'll simulate a scenario whereby, a restaurant receives orders from clients through a graphql endpoint, processes those orders with client payments 
and send emails back to the client if payment either `failed` or `succeeded`.

While at it, we'll create more graphql endpoints, using direct lambda resolvers, in order to mimic a semi real life scenario.

### AWS Services used

#### AWS AppSync
AWS AppSync is a fully managed service allowing developers to deploy scalable and engaging real-time GraphQL backends on AWS.
It leverages WebSockets connections under the hood to provide real time capabilities, by publishing data updates to connected
subscribers.

#### Amazon SQS(Simple Queue Service)
A fully managed message queueing service to decouple producers and consumers.SQS is a fundamental building block for building decoupled architectures

#### AWS Lambda
AWS Lambda is a serverless, event-driven compute service that lets you run code for virtually any type of application or backend service without provisioning or managing servers.
You can trigger Lambda from over 200 AWS services and software as a service (SaaS) applications, and only pay for what you use.

#### AWS StepFunctions
AWS Step Functions is a visual workflow service that helps developers use AWS services to build distributed applications,
automate processes, orchestrate microservices, and create data and machine learning (ML) pipelines.

#### AWS SNS
Amazon Simple Notification Service (SNS) sends notifications two ways, A2A and A2P. A2A provides high-throughput, push-based, many-to-many messaging between distributed systems,
microservices, and event-driven serverless applications. These applications include Amazon Simple Queue Service (SQS), Amazon Kinesis Data Firehose, AWS Lambda, and other HTTPS endpoints.
A2P functionality lets you send messages to your customers with SMS texts, push notifications, and email.

For this application, we'll be using A2P.

#### Amazon DynamoDB
Amazon DynamoDB is a fully managed, serverless, key-value NoSQL database designed to run high-performance applications at any scale.
DynamoDB offers built-in security, continuous backups, automated multi-Region replication, in-memory caching, and data import and export tools.


#### Solutions Architecture


![alt text](https://raw.githubusercontent.com/trey-rosius/event_driven_cdk/master/images/eda_cdk.png)

From the architecture above, the amplify icon signifies a frontend application.It can be a mobile or web app. So a client places
an order for 5 cartoons of pizza from Dominos pizza.

Here's the request payload 
```json
"name": "Pizza",
"quantity": 6,
"restaurantId": "Dominos 
```
AppSync receives the request and sends a message, containing the payload to an attached SQS queue. As we mentioned before, we
use SQS to decouple the event producers(appsync) from the consumers(in this case a Lambda), so that they can communicate asynchronously.

So as order requests keep flooding in, let's say on a world pizza day when demand is really high,all requests are being sent to SQS.
Lambda is a common choice as a consumer for SQS as it supports native integration.So you get to write and maintain less code between 
both of them.

When a Lambda function subscribes to an SQS queue, Lambda polls the queue as it waits for messages to arrive.
Lambda consumes messages in batches, starting at five concurrent batches with five functions at a time.
If there are more messages in the queue, Lambda adds up to 60 functions per minute, up to 1,000 functions, to consume those messages. 
This means that Lambda can scale up to 1,000 concurrent Lambda functions processing messages from the SQS queue

![alt text](https://raw.githubusercontent.com/trey-rosius/event_driven_cdk/master/images/sqs-lambda.png)












All serverless applications are event driven. One service triggers another service, which intern fires off a response.

If you've been in the software world for a while now, which I assume you have, then you've definitely come across the term `coupling` 
numerous times. 

In order to build truly distributed applications, you must make sure your application components aren't tightly coupled. 
D.I

Decouple your application, and then use events and messages to communicate with the various
decoupled parts. That's all. 
This 

In this blog post, we'll look at how to build a modern GraphQL Serverless API using the concept of EDA. 


#### Disclaimer
This application is in no way ready for production purposes.It's only a proof of concept.So please don't forget to destroy all created
resources, once you are done playing with.






## Event Driven Architectures (EDA)

If you've ever built a serverless application, then you've built an event driven application. In simple terms, an EDA is an application 
which emits events, in response to a request. It's now left onto other parts of the application to react to those events.





# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
