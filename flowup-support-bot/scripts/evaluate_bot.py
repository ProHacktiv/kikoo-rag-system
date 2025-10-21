#!/usr/bin/env python3
"""
Script to evaluate bot performance.
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.ticket_processor import TicketProcessor
from src.core.intent_analyzer import IntentAnalyzer
from src.core.response_generator import ResponseGenerator
from src.utils.logger import get_logger


class BotEvaluator:
    """Bot performance evaluator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize evaluator."""
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.ticket_processor = TicketProcessor(config)
        self.intent_analyzer = IntentAnalyzer(config)
        self.response_generator = ResponseGenerator(config)
        
        # Evaluation metrics
        self.metrics = {
            'total_tickets': 0,
            'correct_intent': 0,
            'correct_sentiment': 0,
            'correct_urgency': 0,
            'successful_responses': 0,
            'escalations': 0,
            'processing_times': [],
            'confidence_scores': []
        }
    
    async def evaluate_tickets(self, test_tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate bot performance on test tickets."""
        self.logger.info(f"Evaluating {len(test_tickets)} test tickets")
        
        for ticket_data in test_tickets:
            await self._evaluate_single_ticket(ticket_data)
        
        return self._calculate_metrics()
    
    async def _evaluate_single_ticket(self, ticket_data: Dict[str, Any]):
        """Evaluate a single ticket."""
        self.metrics['total_tickets'] += 1
        
        try:
            # Process ticket
            start_time = datetime.utcnow()
            result = await self.ticket_processor.process_ticket(ticket_data)
            end_time = datetime.utcnow()
            
            processing_time = (end_time - start_time).total_seconds()
            self.metrics['processing_times'].append(processing_time)
            
            # Check intent accuracy
            expected_intent = ticket_data.get('expected_intent')
            predicted_intent = result.get('intent')
            
            if expected_intent and predicted_intent == expected_intent:
                self.metrics['correct_intent'] += 1
            
            # Check sentiment accuracy
            expected_sentiment = ticket_data.get('expected_sentiment')
            predicted_sentiment = result.get('sentiment')
            
            if expected_sentiment and predicted_sentiment == expected_sentiment:
                self.metrics['correct_sentiment'] += 1
            
            # Check urgency accuracy
            expected_urgency = ticket_data.get('expected_urgency')
            predicted_urgency = result.get('urgency')
            
            if expected_urgency and predicted_urgency == expected_urgency:
                self.metrics['correct_urgency'] += 1
            
            # Check response quality
            if result.get('response'):
                self.metrics['successful_responses'] += 1
            
            # Check escalation
            if result.get('escalation_required'):
                self.metrics['escalations'] += 1
            
            # Record confidence
            confidence = result.get('confidence', 0)
            self.metrics['confidence_scores'].append(confidence)
            
        except Exception as e:
            self.logger.error(f"Error evaluating ticket {ticket_data.get('id', 'unknown')}: {str(e)}")
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate evaluation metrics."""
        total = self.metrics['total_tickets']
        
        if total == 0:
            return {}
        
        # Calculate accuracy metrics
        intent_accuracy = self.metrics['correct_intent'] / total if total > 0 else 0
        sentiment_accuracy = self.metrics['correct_sentiment'] / total if total > 0 else 0
        urgency_accuracy = self.metrics['correct_urgency'] / total if total > 0 else 0
        
        # Calculate response metrics
        response_success_rate = self.metrics['successful_responses'] / total if total > 0 else 0
        escalation_rate = self.metrics['escalations'] / total if total > 0 else 0
        
        # Calculate timing metrics
        avg_processing_time = sum(self.metrics['processing_times']) / len(self.metrics['processing_times']) if self.metrics['processing_times'] else 0
        min_processing_time = min(self.metrics['processing_times']) if self.metrics['processing_times'] else 0
        max_processing_time = max(self.metrics['processing_times']) if self.metrics['processing_times'] else 0
        
        # Calculate confidence metrics
        avg_confidence = sum(self.metrics['confidence_scores']) / len(self.metrics['confidence_scores']) if self.metrics['confidence_scores'] else 0
        min_confidence = min(self.metrics['confidence_scores']) if self.metrics['confidence_scores'] else 0
        max_confidence = max(self.metrics['confidence_scores']) if self.metrics['confidence_scores'] else 0
        
        return {
            'total_tickets': total,
            'accuracy': {
                'intent': intent_accuracy,
                'sentiment': sentiment_accuracy,
                'urgency': urgency_accuracy,
                'overall': (intent_accuracy + sentiment_accuracy + urgency_accuracy) / 3
            },
            'response_metrics': {
                'success_rate': response_success_rate,
                'escalation_rate': escalation_rate
            },
            'performance': {
                'avg_processing_time': avg_processing_time,
                'min_processing_time': min_processing_time,
                'max_processing_time': max_processing_time
            },
            'confidence': {
                'avg_confidence': avg_confidence,
                'min_confidence': min_confidence,
                'max_confidence': max_confidence
            }
        }
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate evaluation report."""
        report = []
        report.append("=" * 60)
        report.append("FLOWUP SUPPORT BOT EVALUATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated at: {datetime.utcnow().isoformat()}")
        report.append("")
        
        # Overall metrics
        report.append("OVERALL METRICS")
        report.append("-" * 20)
        report.append(f"Total tickets evaluated: {metrics['total_tickets']}")
        report.append("")
        
        # Accuracy metrics
        report.append("ACCURACY METRICS")
        report.append("-" * 20)
        report.append(f"Intent accuracy: {metrics['accuracy']['intent']:.2%}")
        report.append(f"Sentiment accuracy: {metrics['accuracy']['sentiment']:.2%}")
        report.append(f"Urgency accuracy: {metrics['accuracy']['urgency']:.2%}")
        report.append(f"Overall accuracy: {metrics['accuracy']['overall']:.2%}")
        report.append("")
        
        # Response metrics
        report.append("RESPONSE METRICS")
        report.append("-" * 20)
        report.append(f"Response success rate: {metrics['response_metrics']['success_rate']:.2%}")
        report.append(f"Escalation rate: {metrics['response_metrics']['escalation_rate']:.2%}")
        report.append("")
        
        # Performance metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 20)
        report.append(f"Average processing time: {metrics['performance']['avg_processing_time']:.2f}s")
        report.append(f"Min processing time: {metrics['performance']['min_processing_time']:.2f}s")
        report.append(f"Max processing time: {metrics['performance']['max_processing_time']:.2f}s")
        report.append("")
        
        # Confidence metrics
        report.append("CONFIDENCE METRICS")
        report.append("-" * 20)
        report.append(f"Average confidence: {metrics['confidence']['avg_confidence']:.2f}")
        report.append(f"Min confidence: {metrics['confidence']['min_confidence']:.2f}")
        report.append(f"Max confidence: {metrics['confidence']['max_confidence']:.2f}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 20)
        
        if metrics['accuracy']['overall'] < 0.8:
            report.append("• Consider improving intent classification training")
        
        if metrics['response_metrics']['escalation_rate'] > 0.3:
            report.append("• High escalation rate - review escalation criteria")
        
        if metrics['performance']['avg_processing_time'] > 30:
            report.append("• Processing time is high - consider optimization")
        
        if metrics['confidence']['avg_confidence'] < 0.7:
            report.append("• Low confidence scores - improve training data")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


async def main():
    """Main function to evaluate bot performance."""
    parser = argparse.ArgumentParser(description='Evaluate bot performance')
    parser.add_argument('--config', default='config/settings.yaml', help='Configuration file path')
    parser.add_argument('--test-data', default='tests/fixtures/sample_tickets.json', help='Test data file path')
    parser.add_argument('--output', help='Output file for evaluation report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger(__name__)
    if args.verbose:
        logger.info("Starting bot evaluation")
    
    try:
        # Load configuration
        import yaml
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Load test data
        with open(args.test_data, 'r', encoding='utf-8') as f:
            test_tickets = json.load(f)
        
        # Initialize evaluator
        evaluator = BotEvaluator(config)
        
        # Run evaluation
        logger.info("Running evaluation...")
        metrics = await evaluator.evaluate_tickets(test_tickets)
        
        # Generate report
        report = evaluator.generate_report(metrics)
        
        # Output report
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Evaluation report saved to {args.output}")
        else:
            print(report)
        
        # Save metrics to JSON
        metrics_file = args.output.replace('.txt', '.json') if args.output else 'evaluation_metrics.json'
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"Evaluation metrics saved to {metrics_file}")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
