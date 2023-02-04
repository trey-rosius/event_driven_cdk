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

#### [AWS AppSync](https://aws.amazon.com/appsync/)
AWS AppSync is a fully managed service allowing developers to deploy scalable and engaging real-time GraphQL backends on AWS.
It leverages WebSockets connections under the hood to provide real time capabilities, by publishing data updates to connected
subscribers.

#### [Amazon SQS](https://aws.amazon.com/sqs/)
A fully managed message queueing service to decouple producers and consumers.SQS is a fundamental building block for building decoupled architectures

#### AWS Lambda
AWS Lambda is a serverless, event-driven compute service that lets you run code for virtually any type of application or backend service without provisioning or managing servers.
You can trigger Lambda from over 200 AWS services and software as a service (SaaS) applications, and only pay for what you use.

#### [AWS StepFunctions](https://aws.amazon.com/step-functions/)
AWS Step Functions is a visual workflow service that helps developers use AWS services to build distributed applications,
automate processes, orchestrate microservices, and create data and machine learning (ML) pipelines.

#### [AWS SNS](https://aws.amazon.com/sns/)
Amazon Simple Notification Service (SNS) sends notifications two ways, A2A and A2P. A2A provides high-throughput, push-based, many-to-many messaging between distributed systems,
microservices, and event-driven serverless applications. These applications include Amazon Simple Queue Service (SQS), Amazon Kinesis Data Firehose, AWS Lambda, and other HTTPS endpoints.
A2P functionality lets you send messages to your customers with SMS texts, push notifications, and email.

For this application, we'll be using A2P.

#### [Amazon DynamoDB](https://aws.amazon.com/dynamodb/)
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
This means that Lambda can scale up to 1,000 concurrent Lambda functions processing messages from the SQS queue.

![alt text](https://raw.githubusercontent.com/trey-rosius/event_driven_cdk/master/images/sqs-lambda.png)

Failed messages are sent back into the queue, to be retried by lambda. A DLQ(Dead letter queue) is put in place 
to prevent failed messages from getting added to the queue multiple times. 
Once in DLQ, these messages can be reassessed and resent to the lambda for processing by humans.

Once lambda successfully processes a message, it extracts the order payload and invokes a step functions workflow with the payload 
as the input request.
We use step functions to orchestrate the payment process. No real api's are being called. All we do is mimic a real life scenario. 

Inside the step functions, we randomly determine if an order was paid or not,save the order in dynamoDB and then send `success` or `failure` 
emails using SNS to the client who made the order.

We also create endpoints to `get_order`, `update-order` and `delete-order`.

Enough talk. Let's see some code.

## Prerequisite
Before proceeding, please confirm you have all these dependencies installed on your computer

- [AWS CLI](https://aws.amazon.com/cli/)
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)


### Creating a new cdk python project
From the command line interface(Terminal), create and change directory into the newly created folder using the command

`mkdir eventDrivenCdk && cd $_`

I named my project `eventDrivenCdk`, feel free to give yours a different name.

Within the newly created project,initialize a python cdk project using the command

cdk init --language=python

This project is set up like a standard Python project.  The initialization process also creates a virtualenv 
within this project, stored under the `.venv` directory. 

To create the virtualenv it assumes that there is a `python3` (or `python` for Windows) 
executable in your path with access to the `venv`package. 

If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv manually.

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

Add `boto3` to the `requirements.txt` before running the command.

```
$ pip install -r requirements.txt
```

Boto3 is the aws sdk for python.











## Rererences
- https://aws.amazon.com/blogs/compute/introducing-maximum-concurrency-of-aws-lambda-functions-when-using-amazon-sqs-as-an-event-source/
- https://aws.amazon.com/blogs/compute/understanding-how-aws-lambda-scales-when-subscribed-to-amazon-sqs-queues/
- 





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
