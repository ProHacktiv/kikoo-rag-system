class DeliveryResponseGenerator:
    """Génère des réponses appropriées pour les tickets livraison"""
    
    def __init__(self, odoo: OdooIntegration):
        self.odoo = odoo
        
    def generate_response(self, 
                         user_id: str, 
                         intent: str, 
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère une réponse complète avec actions
        """
        # Récupérer les commandes de l'utilisateur
        orders = self.odoo.get_recent_orders(user_id)
        
        response = {
            'greeting': "Bonjour, je suis l'assistant automatique FlowUp.",
            'body': "",
            'actions': [],
            'escalate': False,
            'escalation_reason': None
        }
        
        if not orders:
            response['body'] = "Je ne trouve aucune commande récente sur votre compte."
            response['escalate'] = True
            response['escalation_reason'] = "Aucune commande trouvée"
            return response
        
        # Prendre la commande la plus récente
        order = orders[0]
        
        # Générer la réponse selon l'intention
        if intent == 'DELIVERY_ESTIMATION':
            response = self._handle_estimation(order, response, context)
        elif intent == 'ORDER_STATUS':
            response = self._handle_status(order, response, context)
        elif intent == 'DELIVERY_PROBLEM':
            response = self._handle_problem(order, response, context)
        elif intent == 'ADDRESS_CHANGE':
            response = self._handle_address_change(order, response, context)
        else:
            response = self._handle_unknown(order, response, context)
            
        return response
    
    def _handle_estimation(self, order: Order, response: Dict, context: Dict) -> Dict:
        """Gère les demandes d'estimation de livraison"""
        
        response['actions'].append('check_order_delay')
        
        if len([order]) > 1:
            response['body'] = f"J'ai trouvé plusieurs commandes sur votre compte. "
            response['body'] += f"Je vais vérifier la plus récente du {order.order_date.strftime('%d/%m/%Y')}.\n\n"
        else:
            response['body'] = f"J'ai trouvé votre commande {order.order_id} du {order.order_date.strftime('%d/%m/%Y')}.\n\n"
        
        if order.is_within_legal_delay:
            days_elapsed = order.days_since_payment
            remaining = order.remaining_days
            
            response['body'] += f"✅ **Votre commande est dans les délais légaux.**\n\n"
            response['body'] += f"• Commandée il y a : {days_elapsed} jours\n"
            response['body'] += f"• Délai maximum : 12 jours ouvrés\n"
            response['body'] += f"• Jours restants : {remaining} jours\n"
            response['body'] += f"• Statut actuel : {order.status.value}\n\n"
            
            # Ajouter info tracking si expédié
            if order.status == OrderStatus.SHIPPED and order.tracking_url:
                response['body'] += f"📦 **Bonne nouvelle !** Votre commande est expédiée.\n"
                response['body'] += f"• Numéro de suivi : {order.tracking_number}\n"
                response['body'] += f"• [Suivre mon colis UPS]({order.tracking_url})\n\n"
                response['actions'].append('provide_tracking')
            
            response['body'] += "Si votre commande n'arrive pas dans les délais, "
            response['body'] += "n'hésitez pas à nous recontacter."
            
        else:
            # Délai dépassé - escalade immédiate
            response['body'] += f"⚠️ **Je constate un dépassement du délai légal** "
            response['body'] += f"({order.days_since_payment} jours).\n\n"
            response['body'] += "Je transfère immédiatement votre demande à un opérateur "
            response['body'] += "pour un traitement prioritaire."
            response['escalate'] = True
            response['escalation_reason'] = f"Délai dépassé: {order.days_since_payment} jours"
            response['actions'].append('escalate_priority')
            
        response['body'] += "\n\nPuis-je vous aider pour autre chose ?"
        return response
    
    def _handle_status(self, order: Order, response: Dict, context: Dict) -> Dict:
        """Gère les demandes de statut de commande"""
        
        response['actions'].append('check_order_status')
        response['body'] = f"Voici le statut de votre commande {order.order_id}:\n\n"
        
        # Icônes par statut
        status_icons = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.PRODUCTION: "🔧",
            OrderStatus.TESTING: "🔍",
            OrderStatus.PICKING: "📦",
            OrderStatus.SHIPPED: "🚚",
            OrderStatus.DELIVERED: "✅"
        }
        
        icon = status_icons.get(order.status, "📋")
        response['body'] += f"{icon} **Statut actuel : {order.status.value.upper()}**\n\n"
        
        # Détails selon le statut
        status_details = {
            OrderStatus.PRODUCTION: "Votre PC est en cours d'assemblage dans nos ateliers.",
            OrderStatus.TESTING: "Votre PC est en phase de test qualité (burn test 24h).",
            OrderStatus.PICKING: "Votre commande est prête et en attente de prise en charge par le transporteur.",
            OrderStatus.SHIPPED: f"Votre colis a été expédié. [Suivre le colis]({order.tracking_url})" if order.tracking_url else "Votre colis a été expédié.",
        }
        
        if order.status in status_details:
            response['body'] += status_details[order.status] + "\n\n"
        
        # Ajouter estimation si pas encore expédié
        if order.status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            response['body'] += f"• Commandé le : {order.order_date.strftime('%d/%m/%Y')}\n"
            response['body'] += f"• Jours écoulés : {order.days_since_payment}/12\n"
            
        response['body'] += "\nPuis-je vous aider pour autre chose ?"
        return response
    
    def _handle_problem(self, order: Order, response: Dict, context: Dict) -> Dict:
        """Gère les problèmes de livraison"""
        
        response['actions'].append('check_delivery_issue')
        
        # Si délai dépassé
        if not order.is_within_legal_delay:
            response['body'] = "Je comprends votre inquiétude concernant votre commande.\n\n"
            response['body'] += f"⚠️ Le délai légal de 12 jours est effectivement dépassé "
            response['body'] += f"({order.days_since_payment} jours).\n\n"
            response['body'] += "Je transfère immédiatement votre réclamation à notre équipe "
            response['body'] += "pour un traitement prioritaire. Un opérateur vous contactera "
            response['body'] += "dans les plus brefs délais."
            response['escalate'] = True
            response['escalation_reason'] = "Problème livraison + délai dépassé"
        else:
            response['body'] = "Je comprends votre préoccupation concernant votre commande.\n\n"
            response['body'] += f"Votre commande {order.order_id} est actuellement "
            response['body'] += f"en statut : **{order.status.value}**\n\n"
            
            if order.status == OrderStatus.SHIPPED:
                response['body'] += "Votre colis a bien été expédié. "
                if order.tracking_url:
                    response['body'] += f"Vous pouvez suivre sa progression : [Tracking UPS]({order.tracking_url})\n\n"
                response['body'] += "Si le colis semble perdu ou bloqué, je vais transférer "
                response['body'] += "votre demande à notre équipe logistique."
                response['escalate'] = True
                response['escalation_reason'] = "Problème avec colis expédié"
            else:
                remaining = order.remaining_days
                response['body'] += f"Nous sommes encore dans les délais légaux "
                response['body'] += f"(il reste {remaining} jours).\n\n"
                response['body'] += "Cependant, si vous avez des inquiétudes particulières, "
                response['body'] += "je peux transférer votre demande à un opérateur."
                
        return response
    
    def _handle_address_change(self, order: Order, response: Dict, context: Dict) -> Dict:
        """Gère les changements d'adresse"""
        
        response['actions'].append('address_change_request')
        response['body'] = "Vous souhaitez modifier l'adresse de livraison.\n\n"
        
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            response['body'] += "⚠️ Votre commande a déjà été expédiée. "
            response['body'] += "Il n'est plus possible de modifier l'adresse.\n\n"
            if order.tracking_url:
                response['body'] += f"Vous pouvez contacter directement UPS : {order.tracking_url}\n\n"
        else:
            response['body'] += "Je transfère votre demande de changement d'adresse "
            response['body'] += "à notre équipe logistique qui pourra effectuer la modification."
            response['escalate'] = True
            response['escalation_reason'] = "Changement d'adresse demandé"
            
        return response
    
    def _handle_unknown(self, order: Order, response: Dict, context: Dict) -> Dict:
        """Gère les cas non identifiés"""
        
        response['body'] = f"Je vois que votre demande concerne votre commande {order.order_id}.\n\n"
        response['body'] += f"• Statut actuel : {order.status.value}\n"
        response['body'] += f"• Commandée le : {order.order_date.strftime('%d/%m/%Y')}\n\n"
        response['body'] += "Pour mieux vous aider, je transfère votre demande à un opérateur."
        response['escalate'] = True
        response['escalation_reason'] = "Demande non identifiée automatiquement"
        
        return response