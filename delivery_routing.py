# -*- coding: utf-8 -*-


from openerp.osv import fields,osv
from openerp.osv import fields, orm
import time
from openerp.report import report_sxw
from netsvc import Service
from openerp.tools.translate import _
import pdb

class delivery_route_class(osv.osv):
    _name = "delivery.routing"
    _description = "Route for Delivery Order"

    def create(self, cr, uid, vals, context=None):
        route_id = self.pool.get('ir.sequence').get(cr,uid,'delivery.route.id')
        vals.update({'name':route_id})

        res=super(delivery_route_class,self).create(cr, uid, vals, context=None)
        return res
        
    def write(self, cr, uid, ids, vals, context=None):
	if 'agents' in vals: 
	    agents = vals['agents']
	    agents_list = agents[0][2]
	    result = []
	    for route in self.browse(cr, uid, ids, context=context):
		
		old_agents_brow = route.agents
		route_id = route.id
		cr.execute('select agent_id from delivery_route_agents_rel where route_id NOT IN %s',(tuple(ids),))
		res1 = cr.fetchall()
		if res1:
			re = map(list, zip(*res1))[0]
			r2 = set(re)
			result = list(r2)
		
		duplicates = set(agents_list).intersection(result)
		if duplicates:
			for agents in self.pool.get('res.partner').browse(cr,uid,agents_list):
				if agents.id in result:
					
					raise osv.except_osv(_('Error!'),_('Agent "%s" already added in route "%s" .')%(agents.name, route.name))

		#pdb.set_trace()
		for line in old_agents_brow:
			if line.id not in agents_list:
				#self.pool.get('res.partner').write(cr, uid, line.id, {'route_id': False})
				cr.execute("UPDATE res_partner SET route_id = NULL WHERE id = %s", (line.id,))


				cr.execute("UPDATE stock_picking SET route_id = NULL WHERE vendor_partner_id = %s", (line.id ,))
				cr.execute("UPDATE account_invoice SET route_id = NULL WHERE partner_id = %s", (line.id,))
				cr.execute('select id from stock_picking where vendor_partner_id = %s',(line.id,))
				ven_ids = cr.fetchall()
				if ven_ids:
					ven = map(list, zip(*ven_ids))[0]
					ven_s = set(ven)
					ven_list = list(ven_s)		
					cr.execute("UPDATE stock_move SET route_id = NULL WHERE picking_id in %s", (tuple(ven_list),))

		#pdb.set_trace()

		cr.execute("UPDATE stock_picking SET route_id = %s WHERE vendor_partner_id IN %s",(tuple(ids),tuple(agents_list),))
		cr.execute("UPDATE account_invoice SET route_id = %s WHERE partner_id IN %s", (tuple(ids),tuple(agents_list),))

		cr.execute("UPDATE res_partner SET route_id = %s WHERE id IN %s", (tuple(ids),tuple(agents_list),))
		cr.execute('select id from stock_picking where vendor_partner_id IN %s',(tuple(agents_list),))
		move_ids = cr.fetchall()
		if move_ids:
			move = map(list, zip(*move_ids))[0]
			mv_s = set(move)
			pick_list = list(mv_s)
			cr.execute("UPDATE stock_move SET route_id = %s WHERE picking_id IN %s", (tuple(ids),tuple(pick_list)))
		#for agents in self.pool.get('res.partner').browse(cr,uid,agents_list):
		#	self.pool.get('res.partner').write(cr, uid, agents.id, {'route_id': ids[0]})
			
		
        return  super(delivery_route_class, self).write(cr, uid, ids, vals, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms picking.
        @return: True
        """
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in pickings:
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)
        return True


    _columns = {
       	'name': fields.char('Route Id', size=64,readonly=True, help="Unique Sequence will generate Automatically once you create & save the form."),
       	'route_name': fields.char('Route Name', size=200,required = True),
        'driver': fields.many2one('res.users', 'Driver',required = True ,help="Select the Driver from Users list."),
	'agents': fields.many2many('res.partner','delivery_route_agents_rel', 'route_id', 'agent_id', 'Agents',help="Select the Agents from Partners list."),
        #'agent': fields.many2one('res.partner', 'Agent',required = True,help="Select the Agent from Partners list."),
        'comment': fields.text("Comment"),
	'active':fields.boolean("Active"),
         }

    _defaults = {
	'active':True,
    }

delivery_route_class()

# Wizard to set the selected user as estimation responsible----start


class set_route_name(osv.osv):
    _name = "set.route.name"
    _description = "To Set the new route name"


    def set_selected_route_name(self, cr, uid, ids, context=None):
        value={}        
        routing_obj = self.pool.get("delivery.routing")
        self_browse = self.browse(cr,uid,ids)
        new_name = self_browse[0].name
        routing_id = context['active_ids']
        routing_brow = routing_obj.browse(cr,uid,routing_id)
        routing_obj.write(cr,uid,routing_id,{'route_name':new_name})
       
        print"new route name------------",new_name
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','delivery.routing'), ('name','=','delivery.routing.form')])
        
        
        value = {
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'delivery.routing',
        'view_id' : view_id,
        'type': 'ir.actions.act_window',
        'res_id': routing_id[0]
     }
        
        return value
    
    _columns = {
              
               'name':fields.char("New Route Name",size=200,required = True),
               
                }

set_route_name()



class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _order = "id desc"

    _columns = {


	'printed':fields.boolean("Printed"),
        }

    _defaults = {
	'printed':False,
    }

stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _order = "id desc"
    _columns = {

	'printed':fields.boolean("Printed"),
        }

    _defaults = {
	'printed':False,
    }

stock_picking_in()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _order = "id desc"

    def _get_route_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
	    if record.vendor_partner_id:
		route = record.vendor_partner_id.route_id
		#cr.execute('select route_id from delivery_route_agents_rel where agent_id =%s', (vendor,))
		#res = cr.fetchone()
		if route:
                	result[record.id] = route.id
		else:
                	result[record.id] = False
            else:
                result[record.id] = False

        return result

    _columns = {
	#'routing_id1': fields.function(_get_route_id, type='many2one', relation="delivery.routing", string="Route",store=True, readonly=True),
	'route_id':fields.related('vendor_partner_id', 'route_id', type='many2one', relation='delivery.routing',store=True, string='Route', readonly=True),
        #'routing_id':fields.many2one("delivery.routing","Route"),
	'printed':fields.boolean("Printed"),
        }

    _defaults = {
	'printed':False,
    }

stock_picking()


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {

	'route_id':fields.many2one("delivery.routing","Routing"),

        }

res_partner()

class account_invoice_form(osv.osv):
    _inherit = 'account.invoice'
    _name = 'account.invoice'	
    _order = "id desc"

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'fq.account.invoice',
            'datas': datas,
            'nodestroy' : True
        }


    _columns = {
	'route_id':fields.related('partner_id', 'route_id', type='many2one', relation='delivery.routing',store=True, string='Route', readonly=True),	
        #'routing_id':fields.many2one("delivery.routing","Route"),
	'printed':fields.boolean("Printed"),
        }

    _defaults = {
	'printed':False,
    }

account_invoice_form()


class pick_list_form(osv.osv):
    _inherit = 'stock.move'
    _order = "id desc"


    _columns = {
	'route_id':fields.related('picking_id', 'route_id', type='many2one', relation='delivery.routing', string='Route', store=True,readonly=True),
       # 'routing_id':fields.many2one("delivery.routing","Route"),
        }

pick_list_form()


# To check the Printed boolen in invoice fter taking reports in paid state
del Service._services['report.account.invoice']

class fq_account_invoice(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(fq_account_invoice, self).__init__(cr, uid, name, context=context)
	
        if 'active_ids' in context:
            invoice_ids = context['active_ids']
	    for invoice in invoice_ids:
            	state = self.pool.get('account.invoice').browse(cr,uid,invoice).state
            	if state == 'paid':
                	self.pool.get('account.invoice').write(cr,uid,invoice,{'printed': True})
	self.localcontext.update({
        'time': time,
    })


report_sxw.report_sxw(
    'report.fq.account.invoice',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser= fq_account_invoice,

)

