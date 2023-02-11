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
Let's say you want to order pizza from a restaurant, through the restaurants mobile or web application. In an ideal scenario, 
the application would let you make(add to cart) your choice of pizza,the quantity you want, with all necessary addons like extra cheese, chilli, and 
only lets you sign in to or create an account when you wish to place the order.

In this tutorial, we'll assume you've already created an account, and you are about to place an order. Once your order has been placed,
we'll run a fake payment check to determine if you've made payment or not, and would email you based on the `success` or 
`failure` of your order payment.

We'll be using a couple of AWS Services to illustrate how all these can be accomplished, in a scalable, decoupled, event driven
manner. 

So stay tuned in

Let's take a quick look at the aws services we'll be using in this application.

### AWS Services

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

🚨Note: We would be looking at code snippets and not the complete source code for the application. For the complete code, please 
visit the GitHub page at [Event Driven CDK](https://github.com/trey-rosius/event_driven_cdk)

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

### Graphql Schema
In the root directory, create a file called `schema.graphql` and type in the following code.
This file is a description of our graphql api. It contains all the types, queries, mutations, subscriptions, etc for our 
graphql api.

```graphql

type Schema {
    query: Query
    mutation: Mutation
}

type Order {

    name: String!
    quantity: Int!
    restaurantId: String!

}

input OrderInput {

    name: String!
    quantity: Int!
    restaurantId: String!
}

input UpdateOrderInput {

    id: String!
    name: String!
    quantity: Int!
    restaurantId: String!
}

type Query {
  orders: [ Order ]!
  order(id: String!): Order!
}

type Mutation {
    postOrder(input: OrderInput!): Order!
    updateOrder(input: UpdateOrderInput!): Order!
    deleteOrder(id: String!): String
}


```
From the schema, our api has  3 mutations and 2 queries.
Before delving into the implementation details of these endpoints, we need to first define all the resources the app needs
in order to run effectively.

### Defining the Graphql API in Stack
The first step is to import the `appsync` class from the `aws-cdk-lib`.
`import aws_cdk.aws_appsync as appsync`

Then, use `CfnGraphQLApi` method within the appsync class to create the api. This method takes a myriad of parameters, 
but for our use case, all we need is an api name, the authentication type, xray and cloud watch for tracing and logging. 


```python
        api = appsync.CfnGraphQLApi(self, "Api",
                                    name="event_driven_cdk",
                                    authentication_type="API_KEY",
                                    xray_enabled=True,
                                    log_config=log_config
                                    )
   log_config = appsync.CfnGraphQLApi.LogConfigProperty(
            cloud_watch_logs_role_arn=appsync_cloud_watch_role.role_arn,
            exclude_verbose_content=False,
            field_log_level="ALL")

```
This line `cloud_watch_logs_role_arn=appsync_cloud_watch_role.role_arn,` gives appsync permissions to push logs to cloudwatch. 
Here's how we define the role and attach its policies.

```python
  cloud_watch_role_full_access = iam.ManagedPolicy.from_managed_policy_arn(self, "cloudWatchLogRole",
                                                                                 'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess')
       
 appsync_cloud_watch_role = iam.Role(self, "AppSyncCloudWatchRole",
                                            assumed_by=iam.ServicePrincipal("appsync.amazonaws.com"),
                                            managed_policies=[
                                                cloud_watch_role_full_access
                                            ])

```
After creating the api, the next logical step is to attach the schema. We use the `CfnGraphQLSchema` method from the appsync
class to achieve this. This method takes in a scope, an id, an api_id which should be a unique aws appsync graphql api identifier and 
a definition(the schema file itself).

```python

dirname = path.dirname(__file__)

with open(os.path.join(dirname, "../schema.graphql"), 'r') as file:
    data_schema = file.read().replace('\n', '')
schema = appsync.CfnGraphQLSchema(scope=self, id="schema", api_id=api.attr_api_id, definition=data_schema)

```

### Defining the Queue
Let's define and attach the sqs queue to appsync. Firstly, we import the sqs class from cdk.

`import aws_cdk.aws_sqs as sqs`

Then, we'll create 2 queues and use one as the Dead letter queue.
```python
        # SQS
        queue = sqs.CfnQueue(
            self, "CdkAccelerateQueue",
            visibility_timeout=300,
            queue_name="sqs-queue"
        )

        deadLetterQueue = sqs.Queue(
            self, "CdkAccelerateDLQueue",
            visibility_timeout=Duration.minutes(10),
            queue_name="dead-letter-queue"
        )

        sqs.DeadLetterQueue(max_receive_count=4, queue=deadLetterQueue)
```

The `visibility_timeout` is the time taken for a consumer to process and delete a message once dequeued. While this timeout is valid,
the message is made unavailable to other consumers. If the timeout expires when the message hasn't been successfully processed
and delivered, the message is sent back into the queue and made available for other consumers to pick up. 

If you don't specify a value for the `visibility_timeout` , AWS CloudFormation uses the default value of 30 seconds. `Default: Duration.seconds(30)`

The `max_receive_count` is the number of times a message can be unsuccesfully dequeued before being moved to the dead-letter queue. We
set the value to 4, meaning after 4 unsuccessful dequeue attempts, that message would be sent to the DLQ.

Now, let's attach the sqs queue to appsync.

`  api.add_dependency(queue)`

That's all. Remember the name of the api we created above was `api`.

### Defining DynamoDB Resources
Import the dynamodb class for cdk.
`import aws_cdk.aws_dynamodb as dynamodb`

Let's create a table called `ORDER` with a composite key. `user_id` for the primary key and `id` as the sort key.



```python
        # DynamoDB
        dynamodb.CfnTable(self, "Table",
                          key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                              attribute_name="user_id",
                              key_type="HASH"
                          ),
                              dynamodb.CfnTable.KeySchemaProperty(
                                  attribute_name="id",
                                  key_type="RANGE"
                              )],
                          billing_mode="PAY_PER_REQUEST",
                          table_name="ORDER",
                          attribute_definitions=[dynamodb.CfnTable.AttributeDefinitionProperty(
                              attribute_name="user_id",
                              attribute_type="S"
                          ),
                              dynamodb.CfnTable.AttributeDefinitionProperty(
                                  attribute_name="id",
                                  attribute_type="S"
                              )]
                          )

```
### Defining SNS Resources
Let's create an SNS topic with topic name `sns-topic`. As usual, we'll import the sns class from aws cdk

 `from aws_cdk import aws_sns as sns`

Then use `CfnTopic` and `CfnTopicPolicy`  methods from the sns class to create and grant policies to the sns topic.

```python 
        cfn_topic = sns.CfnTopic(self, "MyCfnTopic",
                                 display_name="sns-topic",
                                 fifo_topic=False,
                                 topic_name="sns-topic"
                                 )

        sns_publish_policy = sns.CfnTopicPolicy(self, "MyCfnTopicPolicy",
                                                policy_document=iam.PolicyDocument(
                                                    statements=[iam.PolicyStatement(
                                                        actions=["sns:Publish", "sns:Subscribe"
                                                                 ],
                                                        principals=[iam.AnyPrincipal()],
                                                        resources=["*"]
                                                    )]
                                                ),
                                                topics=[cfn_topic.attr_topic_arn]
                                                )
```
Bear in mind that, we've assumed the client is already signed in to our application at this point. So we have their email address.
We'll use the clients email address to subscribe to the sns topic, so that they'll receive email updates on `success` or `failed` payments.

For the purpose of this tutorial, we'll subscribe to sns using an email passed in as a parameter from the commandline, when deploying the application later.

For now, we need to add `email` as a subscriber using `CfnSubscription` method from the sns class.


```python 
        email_address = CfnParameter(self, "subscriptionEmail")
        sns.CfnSubscription(self, "EmailSubscription",
                            topic_arn=cfn_topic.attr_topic_arn,
                            protocol="email",
                            endpoint=email_address.value_as_string

                            )
```

### Step Functions Resources
We won't be looking at how to create a step functions workflow from scratch. I'll assume you at least have a basic understanding of the service.

If you don't, don't worry. I've written a couple of articles to get you up and running in no time.

- [Building Apps with Step Functions](https://phatrabbitapps.com/building-apps-with-step-functions)
- [Building a Step Functions Workflow With CDK, AppSync, and Python](https://phatrabbitapps.com/building-a-step-functions-workflow-with-cdk-appsync-and-python)

The step functions workflow has 4 lambda functions. Here's how it looks like visually. I exported this image from the step functions visual workflow.

![alt text](https://raw.githubusercontent.com/trey-rosius/event_driven_cdk/master/images/stepfunctions_graph.png)

I also exported the workflow as a json file, and saved the file inside a python package called `step_function_workflow` in the project directory.

You can create a python package with same name and get the file here. [workflow.json](https://github.com/trey-rosius/event_driven_cdk/blob/master/step_function_workflow/workflow.json)

For the 4 lambda functions,navigate to the `lambda_fns` folder, create 4 python packages, and within each package, create a python file.
These python files would serve as lambda functions.

1) MODULE NAME: initialize_order, FILE NAME: initialize_order.py 
2) MODULE NAME: process_payment,  FILE NAME: process_payment.py
3) MODULE NAME: complete_order,   FILE NAME: complete_order.py
4) MODULE NAME: cancel_failed_order, FILE NAME: cancel_failed_order.py

Create a file called `step_function.py` within the `step_function_workflow` python package .We'll define all the lambda functions resources needed by the workflow within 
this file.

We have to create a lambda resource for each of the above 4 python files,add them to the step functions workflow and then return a step functions instance.

In order to create a lambda function resource, we need to first import the `aws_lambda` class from cdk.

`from aws_cdk import aws_lambda as lambda_`

Create a function with these parameters. We'll be passing in the stack, lambda permissions and a sns topic we created in the stack file.

`def create_step_function(stack, lambda_step_function_role, cfn_topic):`

Next, using the function `CfnFunction` found within the `aws_lambda` class, let's create the lambda function resource for `initialize_order.py`.

Firstly, we need to return a stream of the lambda function, using the `open` method. We'll repeat these same steps for the other
lambda functions.

```python
with open("lambda_fns/initialize_order/initialize_order.py", 'r') as file:
    initialize_order = file.read()
```

Then, we define the resource the lambda function needs

```python

    initialize_order_function = lambda_.CfnFunction(stack, "initialize-order-function",
                                                    code=lambda_.CfnFunction.CodeProperty(
                                                        zip_file=initialize_order
                                                    ),
                                                    role=lambda_step_function_role.role_arn,

                                                    # the properties below are optional
                                                    architectures=["x86_64"],
                                                    description="lambda-ds",
                                                    environment=lambda_.CfnFunction.EnvironmentProperty(
                                                        variables={
                                                            "ORDER_TABLE": "ORDER",
                                                            "TOPIC_ARN": cfn_topic.attr_topic_arn
                                                        }
                                                    ),
                                                    function_name="initialize-order-function",
                                                    handler="index.handler",
                                                    package_type="Zip",
                                                    runtime="python3.9",
                                                    timeout=123,
                                                    tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                                        mode="Active"
                                                    )
                                                    )

```

Here's what's happening in the above code.

To Create a lambda function, we need a deployment package and an execution role. Our deployment package in this case is a zip file, 
containing the `initialize_order` lambda code.You can also use a container image as your deployment package.

```
code=lambda_.CfnFunction.CodeProperty(zip_file=initialize_order),
```

We also need an execution role which grants the function permission to access other aws services such as step functions, cloudwatch etc

`role=lambda_step_function_role.role_arn,`

Here are the policies we attached to the lambda function role in the stack file.
- Full DynamoDB access(Because we'll be saving the order to the database)
- Full SNS access for sending emails 
- Full CloudWatch access for logging
- 
```python
        lambda_step_function_role = iam.Role(self, "LambdaStepFunctionRole",
                                             assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                             managed_policies=[db_full_access_role,
                                                               cloud_watch_role_full_access,
                                                               sns_policy])

```
Then we set the environment variables that we'll be needing in our lambda function.In this case, it's the dynamodb tablename and sns topic amazon resource
name(arn).

Next, we state the runtime(python 3.9),handler name(which we'll define later within initialize_order.py file, the lambda timeout in seconds. Note that a lambda function can't run above 15 minutes.

Repeat this same steps for the other 3 lambda functions.

Use the file on github as a reference.[step_function.py](https://github.com/trey-rosius/event_driven_cdk/blob/master/step_function_workflow/step_function.py)

At the bottom of the `step_function.py` file, we have to define the step functions workflow template and also add the created lambda functions arn's.

```python
 sf_workflow = Template(workflow).substitute(InitializeOrderArn=initialize_order_function.attr_arn,
                                                ProcessPaymentArn=process_payment_function.attr_arn,
                                                CompleteOrderArn=complete_order_function.attr_arn,
                                                CancelFailedOrderArn=cancel_failed_order_function.attr_arn, dollar="$")

    return sf_workflow
```
Inside the `workflow.json` file, there's a line like this 

`"FunctionName": "$InitializeOrderArn"`

We use the `substitute` method above to replace that line with the arn to where the lambda function resides `InitializeOrderArn=initialize_order_function.attr_arn`.

Now, go to the stack file of your application, and type in the following code to create a step functions state machine.
Firstly, we need to call the `create_step_function(self, lambda_step_function_role, cfn_topic)` we defined above and pass it's return type to our statemachine's definition.

Also, the state machine needs permissions to interact with other aws services. So we grant step functions permissions to execute lambda functions.

```python
        workflow = create_step_function(self, lambda_step_function_role, cfn_topic)

        simple_state_machine = stepfunctions.CfnStateMachine(self, "SimpleStateMachine",
                                                             definition=json.loads(workflow),
                                                             role_arn=lambda_execution_role.role_arn
                                                             )
```

At this point, we've created resources for 75% of the application. Let's go ahead and start creating the endpoints to consume these resources.

##  ENDPOINTS
### CREATE ORDER
When a user places an order, a series of events happen
- An appsync Mutation is invoked.The input to the Mutation is bundled and sent as a message to an SQS Queue.
- A Lambda(post order lambda) polls the messages from the SQS Queue,extracts the order information and starts up a step functions workflow with order information as input.
- The Step functions workflow contains 4 different lambdas(Initialize Order, Process Payment, Complete Order, Cancel Order). 
- The Initialize Order function creates a new order in the database.
- The Process Payment lambda randomly assigns a `success` or `failed` payment status to the order. 
- If payment was successful, the complete order lambda update the order in the database and sends an email to the client.
- If payment failed, the order status is updated in the database and an email sent with failed status to the client through the failed email lambda.

Create a python package inside the `lambda-fns` folder called `post_order`. Then inside that folder, create a python file called `post_order.py`.

This lambda function would poll messages from the sqs queue and start a step functions workflow. Therefore, it'll need permission to receive sqs queue messages
and to start a step functions workflow.

Let's define the code within the `post_order.py` file.

```python

def handler(event, context):
    new_order_list = []
    print("event ", event)
    for record in event["Records"]:
        message_id = record["messageId"]
        request_body = json.loads(record["body"])
        order_data = request_body["input"]
        print(f'post_orders reqeust_body {order_data} type: {type(order_data)}')
        sfn_input = assemble_order(message_id, order_data)
        response = start_sfn_exec(sfn_input, message_id)
        print(f'start sfn execution: {response}')
        new_order_list.append(response["executionArn"])
    return new_order_list

```
Messages from a queue are polled as `Records`. We have to iterate over each record in order to extract the order information, assemble the order and use it 
to start a step functions workflow.

`sfn_input = assemble_order(message_id, order_data)` This method simply adds more random data to the created order and returns the order. 

```python
def assemble_order(message_id, order_data):
    now = datetime.now()
    order_data["user_id"] = "demo_user"
    order_data["id"] = message_id
    order_data["orderStatus"] = DEFAULT_ORDER_STATUS
    order_data["createdAt"] = now.isoformat()
    return json.dumps(order_data, cls=DecimalEncoder)
```

`response = start_sfn_exec(sfn_input, message_id)` here's where we start the step functions workflow, using the step function arn and 
the order data as input.

```python 
def start_sfn_exec(sfn_input, sfn_exec_id):
    response = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=sfn_exec_id,
        input=json.dumps(sfn_input, cls=DecimalEncoder)
    )
    print(f'post_orders start sfn_exec_id {sfn_exec_id} and input {sfn_input}')
    return response
```
Now, lets define the resources and permissions this lambda function needs. It's pretty similar to the step functions lambda resources
we defined above.

Within the stack folder, mine is `event_driven_cdk_app` create a file called `post_order_resource.py` and type in the following code.

```python

def create_post_order_lambda_resource(stack, simple_state_machine, sqs_receive_message_role, queue):
    with open("lambda_fns/post_order/post_order.py", 'r') as file:
        post_function_file = file.read()

    post_function = lambda_.CfnFunction(stack, "post",
                                        code=lambda_.CfnFunction.CodeProperty(
                                            zip_file=post_function_file
                                        ),
                                        role=sqs_receive_message_role.role_arn,

                                        # the properties below are optional
                                        architectures=["x86_64"],
                                        description="lambda-ds",
                                        environment=lambda_.CfnFunction.EnvironmentProperty(
                                            variables={
                                                "ORDER_TABLE": "ORDER",
                                                "STATE_MACHINE_ARN": simple_state_machine.attr_arn
                                            }
                                        ),
                                        function_name="post-order-function",
                                        handler="index.handler",
                                        package_type="Zip",
                                        runtime="python3.9",
                                        timeout=123,
                                        tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                            mode="Active"
                                        )
                                        )

    lambda_.EventSourceMapping(scope=stack, id="MyEventSourceMapping",
                               target=post_function,
                               batch_size=5,
                               enabled=True,
                               event_source_arn=queue.attr_arn)

```
It's very identical to the one we defined above, except for the last part 

```python 
    lambda_.EventSourceMapping(scope=stack, id="MyEventSourceMapping",
                               target=post_function,
                               batch_size=5,
                               enabled=True,
                               event_source_arn=queue.attr_arn)
```
Remember, this function is responsible for polling messages from an SQS queue. We subscribe to the sqs queue using the `EventSourceMapping` function 
of the lambda API by passing in the sqs queue arn as the event source `event_source_arn=queue.attr_arn`.

The `batch_size` indicates the amount of messages to be polled from sqs aat a time.

When this function invokes a step function workflow, the first lambda to run in the workflow is the `initialize_order.py` lambda function.

We created the file in the `initialize_order` python package, but we didn't add any code to it. Open up `initialize_order.py` and type in the 
following code.

All we do is save the order to the database and forward the order details to the next function, which is `process_payment.py`
```python 
def persist_order(order_item):
    print(f'persist_order item {order_item} to table {TABLE_NAME}')
    response = table.put_item(Item=order_item)
    message = {"order_status": order_item["orderStatus"], "order_id": order_item["id"]}
    print(f'new order pending payment {message}')
    return {

        "message": json.dumps(order_item, indent=4, cls=DecimalEncoder)
    }

```
You can grab the complete code here 
The `process_payment.py` function randomly assigns a payment state(`ok` or `error`) and an error message if the randomly assigned state was `error`,and then
moves to the next function. 

The next function is determined by a choice state based on the state of the payment. The next function would be `complete_order.py` if the payment 
state was `ok` or it'll be `cancel_failed_order.py` if the payment state was `error`.

In either of these functions, the order is updated in the database, and an email is sent through SNS.

For the complete order function, the order is updated like so

```python
    response = table.update_item(
        Key={
            "user_id": event["saveResults"]["user_id"],
            "id": event["saveResults"]["id"]
        },
        UpdateExpression="set orderStatus = :s",
        ExpressionAttributeValues={
            ":s": order_status
        },
        ReturnValues="UPDATED_NEW"
    )
```
And an email is sent as such

```python 

  sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message),
        Subject=f'Orders-App: Update for order {message["order_id"]}'

    )
```
See the complete code here [complete_order](https://github.com/trey-rosius/event_driven_cdk/tree/master/lambda_fns/complete_order)

Same thing with `cancel_failed_order.py` function [Cancel Failed Order](https://github.com/trey-rosius/event_driven_cdk/blob/master/lambda_fns/cancel_failed_order/cancel_failed_order.py)











## References
- https://aws.amazon.com/blogs/compute/introducing-maximum-concurrency-of-aws-lambda-functions-when-using-amazon-sqs-as-an-event-source/
- https://aws.amazon.com/blogs/compute/understanding-how-aws-lambda-scales-when-subscribed-to-amazon-sqs-queues/
- 
