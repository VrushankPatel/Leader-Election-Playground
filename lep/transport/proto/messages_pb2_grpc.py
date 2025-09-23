# Generated gRPC service (simplified)

import grpc
from .messages_pb2 import *

class LeaderElectionStub:
    def __init__(self, channel):
        self.RequestVote = channel.unary_unary(
            '/lep.transport.LeaderElection/RequestVote',
            request_serializer=VoteRequest.SerializeToString,
            response_deserializer=VoteResponse.FromString,
        )
        self.AppendEntries = channel.unary_unary(
            '/lep.transport.LeaderElection/AppendEntries',
            request_serializer=AppendEntries.SerializeToString,
            response_deserializer=VoteResponse.FromString,
        )
        self.SendHeartbeat = channel.unary_unary(
            '/lep.transport.LeaderElection/SendHeartbeat',
            request_serializer=Heartbeat.SerializeToString,
            response_deserializer=VoteResponse.FromString,
        )
        self.AnnounceLeader = channel.unary_unary(
            '/lep.transport.LeaderElection/AnnounceLeader',
            request_serializer=LeaderAnnounce.SerializeToString,
            response_deserializer=VoteResponse.FromString,
        )

class LeaderElectionServicer:
    async def RequestVote(self, request, context):
        raise NotImplementedError

    async def AppendEntries(self, request, context):
        raise NotImplementedError

    async def SendHeartbeat(self, request, context):
        raise NotImplementedError

    async def AnnounceLeader(self, request, context):
        raise NotImplementedError

def add_LeaderElectionServicer_to_server(servicer, server):
    server.add_generic_rpc_handlers(
        ('/lep.transport.LeaderElection/RequestVote', servicer.RequestVote),
        ('/lep.transport.LeaderElection/AppendEntries', servicer.AppendEntries),
        ('/lep.transport.LeaderElection/SendHeartbeat', servicer.SendHeartbeat),
        ('/lep.transport.LeaderElection/AnnounceLeader', servicer.AnnounceLeader),
    )