import { Component, TemplateRef } from '@angular/core';
import { ToastService } from '../toast.service';

@Component({
  selector: 'app-toast-global',
  templateUrl: './toast-global.component.html',
  styleUrls: ['./toast-global.component.scss']
})
export class ToastGlobalComponent {
	constructor(public toastService: ToastService) {}

	isTemplate(toast: any) {
		return toast.textOrTpl instanceof TemplateRef;
	}
}
