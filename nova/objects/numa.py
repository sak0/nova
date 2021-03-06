#    Copyright 2014 Red Hat Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo.serialization import jsonutils

from nova.objects import base
from nova.objects import fields
from nova.virt import hardware


class NUMACell(base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'id': fields.IntegerField(read_only=True),
        'cpuset': fields.SetOfIntegersField(),
        'memory': fields.IntegerField(),
        'cpu_usage': fields.IntegerField(default=0),
        'memory_usage': fields.IntegerField(default=0),
        }

    def _to_dict(self):
        return {
            'id': self.id,
            'cpus': hardware.format_cpu_spec(
                self.cpuset, allow_ranges=False),
            'mem': {
                'total': self.memory,
                'used': self.memory_usage},
            'cpu_usage': self.cpu_usage}

    @classmethod
    def _from_dict(cls, data_dict):
        cpuset = hardware.parse_cpu_spec(
            data_dict.get('cpus', ''))
        cpu_usage = data_dict.get('cpu_usage', 0)
        memory = data_dict.get('mem', {}).get('total', 0)
        memory_usage = data_dict.get('mem', {}).get('used', 0)
        cell_id = data_dict.get('id')
        return cls(id=cell_id, cpuset=cpuset, memory=memory,
                   cpu_usage=cpu_usage, memory_usage=memory_usage)


class NUMATopology(base.NovaObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'cells': fields.ListOfObjectsField('NUMACell'),
        }

    obj_relationships = {
        'NUMACell': [('1.0', '1.0')]
    }

    @classmethod
    def obj_from_primitive(cls, primitive):
        if 'nova_object.name' in primitive:
            obj_topology = super(NUMATopology, cls).obj_from_primitive(
                primitive)
        else:
            # NOTE(sahid): This compatibility code needs to stay until we can
            # guarantee that there are no cases of the old format stored in
            # the database (or forever, if we can never guarantee that).
            obj_topology = NUMATopology._from_dict(primitive)
        return obj_topology

    def _to_json(self):
        return jsonutils.dumps(self.obj_to_primitive())

    @classmethod
    def obj_from_db_obj(cls, db_obj):
        return cls.obj_from_primitive(
            jsonutils.loads(db_obj))

    def __len__(self):
        """Defined so that boolean testing works the same as for lists."""
        return len(self.cells)

    def _to_dict(self):
        # TODO(sahid): needs to be removed.
        return {'cells': [cell._to_dict() for cell in self.cells]}

    @classmethod
    def _from_dict(cls, data_dict):
        return cls(cells=[
            NUMACell._from_dict(cell_dict)
            for cell_dict in data_dict.get('cells', [])])
